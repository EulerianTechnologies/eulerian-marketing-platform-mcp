#!/usr/bin/env python3
"""Eulerian Marketing Platform MCP Proxy Server.

This server acts as a transparent proxy between local MCP clients (Claude Desktop, etc.)
and a remote Eulerian Marketing Platform MCP server via HTTP.

It forwards ALL MCP requests directly to the remote server, making all remote tools
and resources available to the client without any intermediary logic.
"""

import os
import sys
import json
import logging
import tempfile
from datetime import datetime
import httpx

# Configuration
EMP_API_ENDPOINT = os.environ.get("EMP_API_ENDPOINT")
EMP_API_TOKEN = os.environ.get("EMP_API_TOKEN")

# Logging setup - Use cross-platform temp directory
DEFAULT_LOG_FILE = os.path.join(tempfile.gettempdir(), "eulerian-mcp-proxy.log")
LOG_FILE = os.environ.get("EMP_LOG_FILE", DEFAULT_LOG_FILE)

# Ensure log directory exists
log_dir = os.path.dirname(LOG_FILE)
if log_dir:
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


def forward_request(request_data: dict) -> dict:
    """Forward a JSON-RPC request to the remote MCP server.
    
    Args:
        request_data: The JSON-RPC request to forward
        
    Returns:
        The JSON-RPC response from the remote server
    """
    timeout = float(os.environ.get("EMP_TIMEOUT", "300"))
    
    request_id = request_data.get("id")
    method = request_data.get("method")
    
    logger.info(f">>> REQUEST: {method} (id: {request_id})")
    logger.debug(f"    Full request: {json.dumps(request_data)[:200]}...")
    
    try:
        logger.info(f"Forwarding to {EMP_API_ENDPOINT}")
        
        # Use httpx for sync HTTP request
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                EMP_API_ENDPOINT,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {EMP_API_TOKEN}"
                },
                json=request_data
            )
        
        logger.info(f"<<< RESPONSE: HTTP {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
            logger.error(f"    Error: {response.text[:200]}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": error_msg
                }
            }
        
        # Parse response
        try:
            response_data = response.json()
            logger.debug(f"    Response: {json.dumps(response_data)[:200]}...")
            
            # Validate JSON-RPC response
            if "jsonrpc" not in response_data:
                logger.warning("    WARNING: Missing 'jsonrpc' field")
            
            if "result" in response_data:
                logger.info("    Has 'result' field [OK]")
            elif "error" in response_data:
                logger.info(f"    Has 'error' field: {response_data['error']}")
            
            return response_data
            
        except json.JSONDecodeError as e:
            logger.error(f"    ERROR: Invalid JSON - {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32700,
                    "message": f"Invalid JSON: {str(e)}"
                }
            }
    
    except httpx.TimeoutException:
        logger.error("ERROR: Request timeout")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Request timeout"
            }
        }
    
    except httpx.RequestError as e:
        logger.error(f"ERROR: Request failed - {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": f"Request failed: {str(e)}"
            }
        }
    
    except Exception as e:
        logger.error(f"ERROR: Unexpected error - {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": f"Error: {str(e)}"
            }
        }


def main() -> None:
    """Entry point for the MCP proxy server.
    
    Runs a transparent stdio proxy that forwards all JSON-RPC requests
    to the remote Eulerian MCP server.
    """
    # Validate configuration
    validate_config()
    
    logger.info("=== EULERIAN MCP PROXY START ===")
    logger.info(f"Endpoint: {EMP_API_ENDPOINT}")
    logger.info(f"Token: {EMP_API_TOKEN[:10] if EMP_API_TOKEN else 'None'}...")
    logger.info(f"Timeout: {float(os.environ.get('EMP_TIMEOUT', '300'))}s")
    logger.info("Starting stdio proxy - all remote tools will be available")
    
    # Set stdout to unbuffered mode
    sys.stdout.reconfigure(line_buffering=True)
    
    try:
        # Read from stdin line by line
        while True:
            try:
                line = sys.stdin.readline()
                
                # Check for EOF
                if not line:
                    logger.info("EOF received on stdin, exiting")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse request
                    request_data = json.loads(line)
                    
                    # Forward to remote server
                    response_data = forward_request(request_data)
                    
                    # JSON-RPC notifications MUST NOT be answered
                    if "id" in request_data and request_data["id"] is not None:
                        response_json = json.dumps(response_data)
                        print(response_json, flush=True)
                        sys.stdout.flush()
                        logger.info("    Response forwarded [OK]")
                    else:
                        logger.info("    Notification forwarded (no response sent)") 
                except json.JSONDecodeError as e:
                    logger.error(f"ERROR: Invalid JSON in request - {e}")
                    logger.error(f"    Problematic line: {line[:200]}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    sys.stdout.flush()
                
                except Exception as e:
                    logger.error(f"ERROR: Unexpected error processing request - {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32000,
                            "message": f"Error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    sys.stdout.flush()
                    
            except EOFError:
                logger.info("EOF on stdin, exiting")
                break
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
                break
            except Exception as e:
                logger.error(f"ERROR in main loop: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Don't break - try to continue
                continue
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        logger.info("=== EULERIAN MCP PROXY SHUTDOWN ===")


if __name__ == "__main__":
    main()

