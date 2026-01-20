#!/usr/bin/env python3
"""Eulerian Marketing Platform MCP Proxy Server.

This server acts as a proxy/bridge between local MCP clients (Claude Desktop, Gemini CLI, etc.)
and a remote Eulerian Marketing Platform MCP server via HTTP.

It uses EMP_API_ENDPOINT and EMP_API_TOKEN environment variables to authenticate
and forward requests to the remote MCP server.
"""

import os
import sys
import json
import logging
import tempfile
from datetime import datetime
from typing import Any
from pathlib import Path
import httpx

from mcp.server.fastmcp import FastMCP
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Configuration
EMP_API_ENDPOINT = os.environ.get("EMP_API_ENDPOINT")
EMP_API_TOKEN = os.environ.get("EMP_API_TOKEN")

# Logging setup - Use cross-platform temp directory
# Default to system temp directory if EMP_LOG_FILE not set
DEFAULT_LOG_FILE = os.path.join(tempfile.gettempdir(), "eulerian-mcp-proxy.log")
LOG_FILE = os.environ.get("EMP_LOG_FILE", DEFAULT_LOG_FILE)

# Ensure log directory exists
log_dir = os.path.dirname(LOG_FILE)
if log_dir:  # Only create if there's a directory part
    os.makedirs(log_dir, exist_ok=True)

# Configure logging to file and stderr with UTF-8 encoding for cross-platform compatibility
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

# For stderr, use system encoding with error handling
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)


def validate_config() -> None:
    """Validate that required environment variables are set."""
    missing_vars = []
    
    if not EMP_API_ENDPOINT:
        missing_vars.append("EMP_API_ENDPOINT")
    if not EMP_API_TOKEN:
        missing_vars.append("EMP_API_TOKEN")
    
    if missing_vars:
        logger.error("The following required environment variables are missing:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("\nPlease set these environment variables before running the server.")
        logger.error("Example:")
        logger.error("  export EMP_API_ENDPOINT=https://your-eulerian-instance.com/api/mcp")
        logger.error("  export EMP_API_TOKEN=your_authentication_token")
        sys.exit(1)


class EulerianMCPProxy:
    """Proxy that forwards MCP requests to remote Eulerian server."""
    
    def __init__(self):
        """Initialize the proxy with configuration."""
        self.endpoint = EMP_API_ENDPOINT
        self.token = EMP_API_TOKEN
        self.timeout = float(os.environ.get("EMP_TIMEOUT", "300"))
        
        logger.info("=== EULERIAN MCP PROXY START ===")
        logger.info(f"Endpoint: {self.endpoint}")
        logger.info(f"Token: {self.token[:10] if self.token else 'None'}...")
        logger.info(f"Timeout: {self.timeout}s")
    
    async def forward_request(self, method: str, params: dict = None) -> dict[str, Any]:
        """Forward a JSON-RPC request to the remote MCP server.
        
        Args:
            method: The JSON-RPC method name
            params: The parameters for the method
            
        Returns:
            The response from the remote server
            
        Raises:
            Exception: If the request fails
        """
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
        }
        if params:
            request_data["params"] = params
        
        logger.info(f">>> REQUEST: {method}")
        logger.debug(f"    Full request: {json.dumps(request_data)[:200]}...")
        
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Forwarding to {self.endpoint}")
                response = await client.post(
                    self.endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}"
                    },
                    json=request_data,
                    timeout=self.timeout
                )
                
                logger.info(f"<<< RESPONSE: HTTP {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
                    logger.error(f"    Error: {response.text[:200]}")
                    raise Exception(error_msg)
                
                response_data = response.json()
                logger.debug(f"    Response: {json.dumps(response_data)[:200]}...")
                
                # Validate JSON-RPC response
                if "jsonrpc" not in response_data:
                    logger.warning("    WARNING: Missing 'jsonrpc' field")
                
                if "result" in response_data:
                    logger.info("    Has 'result' field [OK]")
                    return response_data["result"]
                elif "error" in response_data:
                    logger.error(f"    Has 'error' field: {response_data['error']}")
                    raise Exception(f"Remote error: {response_data['error']}")
                else:
                    logger.warning("    No 'result' or 'error' field")
                    return response_data
                
        except httpx.TimeoutException:
            logger.error("ERROR: Request timeout")
            raise Exception("Request timeout")
        except httpx.RequestError as e:
            logger.error(f"ERROR: Request failed - {str(e)}")
            raise Exception(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"ERROR: Invalid JSON response - {str(e)}")
            raise Exception(f"Invalid JSON response: {str(e)}")


# Dynamically fetch and register tools from remote server
# (Tools are registered in main() to avoid running on import)


def main() -> None:
    """Entry point for the MCP proxy server."""
    # Validate configuration before starting
    validate_config()
    
    # Create proxy and server instances (moved here to avoid running on import)
    global proxy, mcp
    proxy = EulerianMCPProxy()
    mcp = FastMCP("eulerian-marketing-platform")
    
    # Register tools
    @mcp.tool()
    async def list_remote_tools() -> dict[str, Any]:
        """List all available tools from the remote Eulerian MCP server."""
        try:
            result = await proxy.forward_request("tools/list")
            return result
        except Exception as e:
            logger.error(f"Failed to list tools: {str(e)}")
            return {"error": str(e), "tools": []}
    
    @mcp.tool()
    async def call_eulerian_tool(tool_name: str, arguments: dict[str, Any] = None) -> dict[str, Any]:
        """Call a tool on the remote Eulerian MCP server."""
        if arguments is None:
            arguments = {}
        try:
            params = {"name": tool_name, "arguments": arguments}
            result = await proxy.forward_request("tools/call", params)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {str(e)}")
            return {"error": str(e), "tool": tool_name}
    
    @mcp.tool()
    async def get_eulerian_resources() -> dict[str, Any]:
        """List all available resources from the remote Eulerian MCP server."""
        try:
            result = await proxy.forward_request("resources/list")
            return result
        except Exception as e:
            logger.error(f"Failed to list resources: {str(e)}")
            return {"error": str(e), "resources": []}
    
    @mcp.tool()
    async def read_eulerian_resource(uri: str) -> dict[str, Any]:
        """Read a specific resource from the remote Eulerian MCP server."""
        try:
            params = {"uri": uri}
            result = await proxy.forward_request("resources/read", params)
            return result
        except Exception as e:
            logger.error(f"Failed to read resource '{uri}': {str(e)}")
            return {"error": str(e), "uri": uri}
    
    @mcp.tool()
    async def get_server_info() -> dict[str, Any]:
        """Get information about the remote Eulerian MCP server."""
        try:
            result = await proxy.forward_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "eulerian-mcp-proxy", "version": "0.1.1"}
            })
            return result
        except Exception as e:
            logger.error(f"Failed to get server info: {str(e)}")
            return {"error": str(e)}
    
    logger.info("Starting Eulerian MCP Proxy Server...")
    logger.info("Available tools:")
    logger.info("  - list_remote_tools: List all tools from remote server")
    logger.info("  - call_eulerian_tool: Call any remote tool")
    logger.info("  - get_eulerian_resources: List available resources")
    logger.info("  - read_eulerian_resource: Read a specific resource")
    logger.info("  - get_server_info: Get remote server information")
    
    # Run the server in stdio mode (default for MCP)
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
