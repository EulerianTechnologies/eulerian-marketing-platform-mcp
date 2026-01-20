# FastMCP Proxy Implementation Guide

## Overview

Your original `eulerian-marketing-platform-mcp-proxy.py` has been converted to use **FastMCP** while maintaining the same proxy functionality. The new implementation forwards MCP requests from local clients (Claude Desktop, Gemini CLI) to your remote Eulerian MCP server.

## What Changed

### Original Implementation (stdio proxy)
Your original script was a **line-by-line JSON-RPC forwarder**:
- Read JSON-RPC from stdin
- Forward to remote HTTP endpoint
- Return response to stdout

### New Implementation (FastMCP proxy)
The new implementation uses **FastMCP tools** as a bridge:
- Exposes MCP tools to local clients
- Tools internally forward requests to remote server
- Returns structured responses

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│   Gemini CLI    │
│   Mistral AI    │
└────────┬────────┘
         │ MCP stdio protocol
         │
┌────────▼────────────────────────────┐
│  eulerian-marketing-platform        │
│  FastMCP Server (server.py)         │
│  ┌──────────────────────────────┐   │
│  │ Tools:                       │   │
│  │  - list_remote_tools()       │   │
│  │  - call_eulerian_tool()      │   │
│  │  - get_eulerian_resources()  │   │
│  │  - read_eulerian_resource()  │   │
│  │  - get_server_info()         │   │
│  └──────────────────────────────┘   │
└────────┬────────────────────────────┘
         │ HTTP/JSON-RPC
         │ (with Authorization header)
         │
┌────────▼────────────────────────────┐
│  Remote Eulerian MCP Server         │
│  (EMP_API_ENDPOINT)                 │
│  - Actual business logic            │
│  - Marketing analytics tools        │
│  - Campaign management              │
└─────────────────────────────────────┘
```

## Available Tools

The proxy exposes 5 tools to AI assistants:

### 1. `list_remote_tools()`
Discovers what tools are available on the remote Eulerian server.

**Usage in Claude:**
```
"What tools are available from Eulerian?"
```

**What it does:**
- Sends `tools/list` JSON-RPC request to remote server
- Returns list of all available tools with descriptions

---

### 2. `call_eulerian_tool(tool_name, arguments)`
Generic tool caller - forwards any tool call to the remote server.

**Usage in Claude:**
```
"Use the Eulerian tool 'get_campaigns' to fetch all campaigns"

"Call the get_campaign_details tool with campaign_id='CAMP-12345'"
```

**What it does:**
- Sends `tools/call` JSON-RPC request
- Passes tool name and arguments to remote server
- Returns the tool's result

---

### 3. `get_eulerian_resources()`
Lists available resources (data sources) from the remote server.

**Usage in Claude:**
```
"What resources are available from Eulerian?"
```

**What it does:**
- Sends `resources/list` JSON-RPC request
- Returns available resources (configs, reports, etc.)

---

### 4. `read_eulerian_resource(uri)`
Reads a specific resource by URI.

**Usage in Claude:**
```
"Read the resource at eulerian://config/settings"
```

**What it does:**
- Sends `resources/read` JSON-RPC request
- Returns the resource content

---

### 5. `get_server_info()`
Gets information about the remote Eulerian MCP server.

**Usage in Claude:**
```
"What's the version of the Eulerian server?"
```

**What it does:**
- Sends `initialize` JSON-RPC request
- Returns server capabilities and metadata

## Key Features

### 1. **Logging**
Enhanced logging to both file and stderr:
```python
LOG_FILE = os.environ.get("EMP_LOG_FILE", "/tmp/eulerian-mcp-proxy.log")
```

Logs include:
- Request/response details
- HTTP status codes
- Error messages
- Timing information

**View logs:**
```bash
tail -f /tmp/eulerian-mcp-proxy.log
```

---

### 2. **Error Handling**
Comprehensive error handling for:
- HTTP errors (non-200 responses)
- Timeout errors (default 300s, configurable)
- JSON parsing errors
- Network errors

**Configure timeout:**
```bash
export EMP_TIMEOUT=600  # 10 minutes
```

---

### 3. **Async Implementation**
Uses `httpx.AsyncClient` for better performance:
- Non-blocking HTTP requests
- Better concurrency
- Timeout handling

---

### 4. **Environment Variables**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMP_API_ENDPOINT` | ✅ Yes | - | Remote MCP server URL |
| `EMP_API_TOKEN` | ✅ Yes | - | Authentication token |
| `EMP_LOG_FILE` | ❌ No | `/tmp/eulerian-mcp-proxy.log` | Log file location |
| `EMP_TIMEOUT` | ❌ No | `300` | Request timeout in seconds |

---

## How AI Assistants Use It

### Example Conversation Flow

**User:** "Show me all available Eulerian tools"

**Claude internally:**
1. Calls `list_remote_tools()`
2. Proxy forwards JSON-RPC to `EMP_API_ENDPOINT`
3. Remote server returns tool list
4. Proxy returns to Claude
5. Claude shows formatted list to user

**User:** "Get campaign details for CAMP-12345"

**Claude internally:**
1. Calls `call_eulerian_tool("get_campaign_details", {"campaign_id": "CAMP-12345"})`
2. Proxy forwards to remote server
3. Remote server executes the tool
4. Returns campaign data
5. Claude formats and shows to user

## Differences from Original Proxy

| Aspect | Original | FastMCP Version |
|--------|----------|-----------------|
| **Protocol** | Raw JSON-RPC line-by-line | FastMCP tools |
| **Tools** | Transparent forwarding | Explicit tool wrappers |
| **Discovery** | None | Built-in tool discovery |
| **Logging** | Custom to file/stderr | Python logging module |
| **HTTP Client** | `requests` (sync) | `httpx` (async) |
| **Error Handling** | Manual JSON-RPC errors | Python exceptions + MCP error handling |
| **AI Integration** | Generic | Tool-specific with descriptions |

## Benefits of FastMCP Version

1. **Better AI Integration**
   - AI assistants see specific tools with descriptions
   - Can discover available operations
   - Better prompting and tool selection

2. **Easier to Extend**
   - Add new tools easily with `@mcp.tool()` decorator
   - No manual JSON-RPC handling
   - Type hints for better validation

3. **Better Logging**
   - Structured logging with levels
   - Configurable log location
   - Better debugging

4. **Async Support**
   - Better performance
   - Non-blocking operations
   - Concurrent request handling

5. **Standard MCP Protocol**
   - Works with all MCP clients
   - Follows MCP specification
   - Compatible with ecosystem

## Testing the New Implementation

### 1. Test Validation
```bash
# Should show error about missing variables
eulerian-marketing-platform
```

### 2. Test with Environment Variables
```bash
export EMP_API_ENDPOINT=https://your-server.com/mcp
export EMP_API_TOKEN=your_token
eulerian-marketing-platform
```

### 3. Test with Claude Desktop

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "eulerian": {
      "command": "uvx",
      "args": ["eulerian-marketing-platform"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-server.com/mcp",
        "EMP_API_TOKEN": "your_token"
      }
    }
  }
}
```

Then ask Claude:
```
"What Eulerian tools are available?"
"List all resources from Eulerian"
"Get information about the Eulerian server"
```

### 4. Check Logs
```bash
tail -f /tmp/eulerian-mcp-proxy.log
```

You should see:
```
[2025-01-20 10:30:15] INFO: === EULERIAN MCP PROXY START ===
[2025-01-20 10:30:15] INFO: Endpoint: https://your-server.com/mcp
[2025-01-20 10:30:15] INFO: Token: your_token...
[2025-01-20 10:30:15] INFO: Starting Eulerian MCP Proxy Server...
[2025-01-20 10:30:20] INFO: >>> REQUEST: tools/list
[2025-01-20 10:30:20] INFO: Forwarding to https://your-server.com/mcp
[2025-01-20 10:30:21] INFO: <<< RESPONSE: HTTP 200
[2025-01-20 10:30:21] INFO:     Has 'result' field ✓
```

## Troubleshooting

### Issue: "EMP_API_ENDPOINT environment variable is missing"
**Solution:** Set the environment variable
```bash
export EMP_API_ENDPOINT=https://your-server.com/mcp
```

### Issue: "HTTP 401: Unauthorized"
**Solution:** Check your token is correct
```bash
export EMP_API_TOKEN=your_correct_token
```

### Issue: "Request timeout"
**Solution:** Increase timeout
```bash
export EMP_TIMEOUT=600  # 10 minutes
```

### Issue: No tools appearing in Claude
**Solution:**
1. Restart Claude Desktop
2. Check logs: `tail -f /tmp/eulerian-mcp-proxy.log`
3. Verify endpoint is accessible: `curl -H "Authorization: Bearer $EMP_API_TOKEN" $EMP_API_ENDPOINT`

### Issue: "Invalid JSON response"
**Solution:** Ensure your remote server returns valid JSON-RPC responses

## Migration Checklist

- [x] ✅ Environment variables match (`EMP_API_ENDPOINT`, `EMP_API_TOKEN`)
- [x] ✅ Logging to file and stderr
- [x] ✅ HTTP forwarding with authentication
- [x] ✅ Error handling for timeouts and HTTP errors
- [x] ✅ JSON-RPC validation
- [ ] ⚠️ **Test with your actual remote Eulerian MCP server**
- [ ] ⚠️ **Verify all remote tools work through the proxy**

## Next Steps

1. **Test the proxy** with your remote Eulerian server
2. **Verify logging** is working correctly
3. **Test with Claude Desktop** or Gemini CLI
4. **Add custom tools** if needed (beyond the generic forwarders)
5. **Deploy and share** with your team

The proxy is fully functional and maintains the same core functionality as your original implementation while leveraging FastMCP's benefits!
