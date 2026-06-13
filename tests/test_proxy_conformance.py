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

REQUIRED_TOOLS = [
    "getallowedwebsite_account",
    "how_to_query_flat_aggregate_batch_reporting",
    "flat_aggregate_batch_reporting",
    "kinds_batch_reporting",
    "metrics_batch_reporting",
    "dimensions_batch_reporting",
    "segmentations_batch_reporting",
    "ask_documentation_account",
    "eulerian_tool_invoke",
]


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


def test_ping(proxy):
    """ping must identify the Eulerian server and report ok status."""
    resp = rpc(proxy, "ping", req_id=5)
    assert "result" in resp, f"Expected result, got: {resp}"
    result = resp["result"]
    assert result.get("status") == "ok", \
        f"ping status must be 'ok', got: {result.get('status')}"
    assert result.get("server") == "eulerian-marketing-platform", \
        f"ping server must be 'eulerian-marketing-platform', got: {result.get('server')}"
    assert result.get("platform"), \
        f"ping platform must be non-empty, got: {result.get('platform')}"
    assert result.get("timestamp"), \
        f"ping timestamp must be non-empty, got: {result.get('timestamp')}"


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------

def test_tools_list_returns_tools(proxy):
    """tools/list must return a non-empty list of tools."""
    resp = rpc(proxy, "tools/list", req_id=10)
    assert "result" in resp, f"Expected 'result', got: {resp}"
    assert "tools" in resp["result"], "Missing 'tools' key in result"
    assert len(resp["result"]["tools"]) > 0, "Tool list is empty"


def test_required_tools_always_present(proxy):
    """Contract tools must always be present regardless of account or config."""
    resp = rpc(proxy, "tools/list", req_id=11)
    tool_names = {t["name"] for t in resp["result"]["tools"]}
    for required in REQUIRED_TOOLS:
        assert required in tool_names, f"Required tool missing from tools/list: '{required}'"


def test_tools_list_schema_shape(proxy):
    """Every tool must have name, description, and a valid inputSchema per MCP spec."""
    resp = rpc(proxy, "tools/list", req_id=12)
    tools = resp["result"]["tools"]

    for tool in tools:
        name = tool.get("name", "<unnamed>")
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert "description" in tool, f"Tool '{name}' missing 'description'"
        assert "inputSchema" in tool, f"Tool '{name}' missing 'inputSchema'"
        schema = tool["inputSchema"]
        assert isinstance(schema, dict), f"Tool '{name}' inputSchema must be an object"
        assert schema.get("type") == "object", \
            f"Tool '{name}' inputSchema.type must be 'object', got: {schema.get('type')}"
        if "properties" in schema:
            assert isinstance(schema["properties"], dict), \
                f"Tool '{name}' inputSchema.properties must be an object"
        if "required" in schema:
            assert isinstance(schema["required"], list), \
                f"Tool '{name}' inputSchema.required must be an array"
            if "properties" in schema:
                for field in schema["required"]:
                    assert field in schema["properties"], \
                        f"Tool '{name}': required field '{field}' not declared in properties"


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
# Prompts — not implemented, well-defined error contract
# ---------------------------------------------------------------------------

def test_prompts_list_returns_empty(proxy):
    """prompts/list must return an empty array (no prompts implemented)."""
    resp = rpc(proxy, "prompts/list", req_id=60)
    assert "result" in resp, f"Expected result, got: {resp}"
    assert resp["result"].get("prompts") == [], \
        f"prompts/list must return empty array, got: {resp['result'].get('prompts')}"


def test_prompts_get_returns_32602(proxy):
    """prompts/get must return -32602 (Invalid Params) — no prompts are defined."""
    resp = rpc(proxy, "prompts/get", {"name": "nonexistent_prompt"}, req_id=61)
    assert "error" in resp, f"Expected JSON-RPC error, got: {resp}"
    assert resp["error"].get("code") == -32602, \
        f"Expected -32602 (Invalid Params), got: {resp['error'].get('code')}"


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

def test_resources_list(proxy):
    """resources/list must return a valid list with uri and name on each entry."""
    resp = rpc(proxy, "resources/list", req_id=70)
    assert "result" in resp, f"Expected result, got: {resp}"
    assert "resources" in resp["result"], "resources/list result must have 'resources' key"
    for resource in resp["result"]["resources"]:
        assert "uri" in resource, f"Resource missing 'uri': {resource}"
        assert "name" in resource, f"Resource missing 'name': {resource}"


def test_resources_read(proxy):
    """resources/read must return contents with uri and text or blob per MCP spec."""
    list_resp = rpc(proxy, "resources/list", req_id=71)
    resources = list_resp["result"]["resources"]

    if not resources:
        pytest.skip("No resources available to read")

    uri = resources[0]["uri"]
    resp = rpc(proxy, "resources/read", {"uri": uri}, req_id=72)
    assert "result" in resp, f"Expected result, got: {resp}"
    assert "contents" in resp["result"], "resources/read result must have 'contents'"
    for item in resp["result"]["contents"]:
        assert "uri" in item, f"Content item missing 'uri': {item}"
        assert "text" in item or "blob" in item, \
            f"Content item must have 'text' or 'blob': {item}"


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
