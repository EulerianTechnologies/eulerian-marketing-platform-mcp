import os
import pytest
import httpx
import json
from typing import AsyncGenerator

EMP_API_ENDPOINT = os.getenv("EMP_API_ENDPOINT")
EMP_API_TOKEN = os.getenv("EMP_API_TOKEN")

# Tools that must always be present regardless of account or configuration
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


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    headers = {
        "Authorization": f"Bearer {EMP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(base_url=EMP_API_ENDPOINT, headers=headers) as client:
        yield client


def print_curl_equivalent(method: str, payload: dict, sse: bool = False):
    headers_str = (
        f"-H 'Authorization: Bearer {EMP_API_TOKEN}' "
        f"-H 'Content-Type: application/json'"
    )
    if sse:
        headers_str += " -H 'Accept: text/event-stream'"
    payload_str = json.dumps(payload)
    print(f"\n# Curl equivalent for {method} {EMP_API_ENDPOINT}:")
    print(f"curl -X {method} {EMP_API_ENDPOINT} \\\n     {headers_str} \\\n     -d '{payload_str}'\n")


# ---------------------------------------------------------------------------
# Handshake
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_initialize(client: httpx.AsyncClient):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "protocolVersion" in data["result"]
    assert "capabilities" in data["result"]
    assert "serverInfo" in data["result"]


@pytest.mark.asyncio
async def test_mcp_ping(client: httpx.AsyncClient):
    payload = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"] == {}, f"ping must return empty object, got: {data['result']}"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_tools_list(client: httpx.AsyncClient):
    payload = {"jsonrpc": "2.0", "id": 10, "method": "tools/list"}
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    assert len(data["result"]["tools"]) > 0


@pytest.mark.asyncio
async def test_mcp_required_tools_always_present(client: httpx.AsyncClient):
    """The contract tools must always be available regardless of account or config."""
    payload = {"jsonrpc": "2.0", "id": 11, "method": "tools/list"}
    response = await client.post("", json=payload)
    tool_names = {t["name"] for t in response.json()["result"]["tools"]}
    for required in REQUIRED_TOOLS:
        assert required in tool_names, f"Required tool missing from tools/list: '{required}'"


@pytest.mark.asyncio
async def test_mcp_tools_input_schema_validity(client: httpx.AsyncClient):
    """Every tool's inputSchema must be a valid JSON Schema object per MCP spec."""
    payload = {"jsonrpc": "2.0", "id": 12, "method": "tools/list"}
    response = await client.post("", json=payload)
    tools = response.json()["result"]["tools"]

    for tool in tools:
        name = tool["name"]
        assert "inputSchema" in tool, f"Tool '{name}' missing inputSchema"
        schema = tool["inputSchema"]

        assert isinstance(schema, dict), \
            f"Tool '{name}': inputSchema must be an object"
        assert schema.get("type") == "object", \
            f"Tool '{name}': inputSchema.type must be 'object', got '{schema.get('type')}'"

        if "properties" in schema:
            assert isinstance(schema["properties"], dict), \
                f"Tool '{name}': inputSchema.properties must be an object"

        if "required" in schema:
            assert isinstance(schema["required"], list), \
                f"Tool '{name}': inputSchema.required must be an array"
            if "properties" in schema:
                for field in schema["required"]:
                    assert field in schema["properties"], \
                        f"Tool '{name}': required field '{field}' not declared in properties"


@pytest.mark.asyncio
async def test_mcp_tool_call_json(client: httpx.AsyncClient):
    payload = {
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/call",
        "params": {
            "name": "eulerian_tool_invoke",
            "arguments": {"tool_name": "getallowedwebsite_account", "arguments": {}},
        },
    }
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "content" in data["result"], "tools/call result must have a content array"


@pytest.mark.asyncio
async def test_mcp_tool_call_sse(client: httpx.AsyncClient):
    payload = {
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/call",
        "params": {
            "name": "eulerian_tool_invoke",
            "arguments": {"tool_name": "getallowedwebsite_account", "arguments": {}},
        },
    }
    print_curl_equivalent("POST", payload, sse=True)

    headers = {"Accept": "text/event-stream"}
    async with client.stream("POST", "", json=payload, headers=headers) as response:
        assert response.status_code == 200

        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type, \
            f"Expected Content-Type: text/event-stream, got: {content_type}"

        events = []
        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk
            while "\n\n" in buffer:
                event_block, buffer = buffer.split("\n\n", 1)
                for line in event_block.splitlines():
                    if line.startswith("data:"):
                        raw = line[len("data:"):].strip()
                        if raw and raw != "[DONE]":
                            events.append(json.loads(raw))

        assert len(events) > 0, "No SSE events received"

        for event in events:
            assert event.get("jsonrpc") == "2.0", f"SSE event missing jsonrpc field: {event}"
            assert "result" in event or "error" in event, \
                f"SSE event must have result or error: {event}"

        results = [e for e in events if "result" in e and e.get("id") == 14]
        assert len(results) > 0, "No SSE event matched request id=14"
        assert "content" in results[0]["result"], \
            f"Tool result must have content array: {results[0]}"


# ---------------------------------------------------------------------------
# Prompts — not implemented, well-defined error contract
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_prompts_list_returns_empty(client: httpx.AsyncClient):
    """prompts/list must return an empty array (no prompts implemented)."""
    payload = {"jsonrpc": "2.0", "id": 20, "method": "prompts/list"}
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data, f"Expected result, got: {data}"
    assert data["result"].get("prompts") == [], \
        f"prompts/list must return empty array, got: {data['result'].get('prompts')}"


@pytest.mark.asyncio
async def test_mcp_prompts_get_returns_32602(client: httpx.AsyncClient):
    """prompts/get must return -32602 (Invalid Params) — no prompts are defined."""
    payload = {
        "jsonrpc": "2.0",
        "id": 21,
        "method": "prompts/get",
        "params": {"name": "nonexistent_prompt"},
    }
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "error" in data, f"Expected JSON-RPC error, got: {data}"
    assert data["error"]["code"] == -32602, \
        f"Expected -32602 (Invalid Params), got: {data['error']['code']}"


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_resources_list(client: httpx.AsyncClient):
    """resources/list must return a valid list with uri and name on each entry."""
    payload = {"jsonrpc": "2.0", "id": 30, "method": "resources/list"}
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data, f"Expected result, got: {data}"
    assert "resources" in data["result"], "resources/list result must have 'resources' key"
    for resource in data["result"]["resources"]:
        assert "uri" in resource, f"Resource missing 'uri': {resource}"
        assert "name" in resource, f"Resource missing 'name': {resource}"


@pytest.mark.asyncio
async def test_mcp_resources_read(client: httpx.AsyncClient):
    """resources/read must return contents with uri and text or blob per MCP spec."""
    list_response = await client.post("", json={"jsonrpc": "2.0", "id": 31, "method": "resources/list"})
    resources = list_response.json()["result"]["resources"]

    if not resources:
        pytest.skip("No resources available to read")

    uri = resources[0]["uri"]
    payload = {"jsonrpc": "2.0", "id": 32, "method": "resources/read", "params": {"uri": uri}}
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data, f"Expected result, got: {data}"
    assert "contents" in data["result"], "resources/read result must have 'contents'"
    for item in data["result"]["contents"]:
        assert "uri" in item, f"Content item missing 'uri': {item}"
        assert "text" in item or "blob" in item, \
            f"Content item must have 'text' or 'blob': {item}"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_unknown_method_returns_32601(client: httpx.AsyncClient):
    """Unknown methods must return -32601 (Method Not Found) per JSON-RPC spec."""
    payload = {"jsonrpc": "2.0", "id": 40, "method": "nonexistent/method"}
    print_curl_equivalent("POST", payload)
    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "error" in data, f"Expected error for unknown method, got: {data}"
    assert data["error"]["code"] == -32601, \
        f"Expected -32601 (Method Not Found), got: {data['error']['code']}"
