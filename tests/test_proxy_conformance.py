"""
End-to-end proxy conformance tests.

Spawns the proxy subprocess, communicates over stdin/stdout, and validates
MCP spec compliance of the full chain (proxy + remote server).

Requires EMP_API_ENDPOINT and EMP_API_TOKEN env vars — skipped otherwise.
"""
import os
import sys
import json
import subprocess
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("EMP_API_ENDPOINT") or not os.getenv("EMP_API_TOKEN"),
    reason="EMP_API_ENDPOINT and EMP_API_TOKEN required",
)

MCP_PROTOCOL_VERSION = "2024-11-05"


@pytest.fixture(scope="module")
def proxy():
    """Start the proxy subprocess once per module, terminate after all tests."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "eulerian_marketing_platform.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=os.environ.copy(),
    )
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def rpc(proc, method, params=None, req_id=1):
    """Send a JSON-RPC request and return the parsed response."""
    request = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        request["params"] = params
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    assert line, f"Proxy returned no response for method '{method}'"
    return json.loads(line)


# ---------------------------------------------------------------------------
# Protocol handshake
# ---------------------------------------------------------------------------

def test_initialize_response_shape(proxy):
    """initialize must return protocolVersion, capabilities, and serverInfo."""
    resp = rpc(proxy, "initialize", {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": "ci-conformance-test", "version": "1.0.0"},
    })
    assert resp.get("jsonrpc") == "2.0"
    assert resp.get("id") == 1
    assert "result" in resp, f"Expected 'result', got: {resp}"

    result = resp["result"]
    assert "protocolVersion" in result, "Missing protocolVersion"
    assert "capabilities" in result, "Missing capabilities"
    assert "serverInfo" in result, "Missing serverInfo"


def test_initialized_notification_does_not_crash(proxy):
    """notifications/initialized must be silently accepted (no response expected)."""
    notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    proxy.stdin.write(json.dumps(notification) + "\n")
    proxy.stdin.flush()
    # No response expected — proxy must not crash. Verified implicitly by subsequent tests.


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------

def test_tools_list_returns_tools(proxy):
    """tools/list must return a non-empty list of tools."""
    resp = rpc(proxy, "tools/list", req_id=10)
    assert "result" in resp, f"Expected 'result', got: {resp}"
    assert "tools" in resp["result"], "Missing 'tools' key in result"
    assert len(resp["result"]["tools"]) > 0, "Tool list is empty"


def test_tools_list_schema_shape(proxy):
    """Every tool must have name, description, and a valid inputSchema per MCP spec."""
    resp = rpc(proxy, "tools/list", req_id=11)
    tools = resp["result"]["tools"]

    for tool in tools:
        name = tool.get("name", "<unnamed>")
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert "description" in tool, f"Tool '{name}' missing 'description'"
        assert "inputSchema" in tool, f"Tool '{name}' missing 'inputSchema'"
        schema = tool["inputSchema"]
        assert isinstance(schema, dict), f"Tool '{name}' inputSchema must be an object"
        assert schema.get("type") == "object", (
            f"Tool '{name}' inputSchema.type must be 'object', got: {schema.get('type')}"
        )


# ---------------------------------------------------------------------------
# Tool invocation
# ---------------------------------------------------------------------------

def test_tool_call_response_shape(proxy):
    """tools/call must return a result with a 'content' array."""
    tools_resp = rpc(proxy, "tools/list", req_id=20)
    first_tool = tools_resp["result"]["tools"][0]["name"]

    resp = rpc(proxy, "tools/call", {
        "name": first_tool,
        "arguments": {},
    }, req_id=21)

    assert "result" in resp or "error" in resp, f"Response must have 'result' or 'error': {resp}"
    if "result" in resp:
        assert "content" in resp["result"], (
            f"tools/call result must have 'content' array per MCP spec, got: {resp['result']}"
        )


def test_tool_call_unknown_tool_returns_error(proxy):
    """Calling a non-existent tool must signal failure.

    Per MCP spec, servers may return either a JSON-RPC error or a result
    with isError=true — both are valid tool-level error representations.
    """
    resp = rpc(proxy, "tools/call", {
        "name": "__nonexistent_tool__",
        "arguments": {},
    }, req_id=30)
    is_jsonrpc_error = "error" in resp
    is_tool_error = (
        "result" in resp
        and resp["result"].get("isError") is True
    )
    assert is_jsonrpc_error or is_tool_error, (
        f"Expected error or isError=true for unknown tool, got: {resp}"
    )


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_unknown_method_returns_method_not_found(proxy):
    """Unknown methods must return error code -32601 (Method Not Found)."""
    resp = rpc(proxy, "nonexistent/method", req_id=40)
    assert "error" in resp, f"Expected error for unknown method, got: {resp}"
    assert resp["error"].get("code") == -32601, (
        f"Expected -32601 (Method Not Found), got: {resp['error'].get('code')}"
    )


def test_invalid_json_returns_parse_error(proxy):
    """Malformed JSON on stdin must return error code -32700 (Parse Error)."""
    proxy.stdin.write("this is not valid json\n")
    proxy.stdin.flush()
    line = proxy.stdout.readline()
    resp = json.loads(line)
    assert "error" in resp
    assert resp["error"].get("code") == -32700, (
        f"Expected -32700 (Parse Error), got: {resp['error'].get('code')}"
    )


# ---------------------------------------------------------------------------
# JSON-RPC envelope
# ---------------------------------------------------------------------------

def test_response_always_includes_jsonrpc_field(proxy):
    """Every response must include jsonrpc: '2.0' per the JSON-RPC spec."""
    resp = rpc(proxy, "tools/list", req_id=50)
    assert resp.get("jsonrpc") == "2.0", (
        f"Response missing jsonrpc field or wrong version: {resp}"
    )


def test_response_id_matches_request(proxy):
    """Response id must match the request id."""
    resp = rpc(proxy, "tools/list", req_id=99)
    assert resp.get("id") == 99, f"Response id mismatch: expected 99, got {resp.get('id')}"
