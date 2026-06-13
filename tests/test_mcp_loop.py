import os
import pytest
import httpx
import json
from typing import AsyncGenerator

# Environment variables
EMP_API_ENDPOINT = os.getenv("EMP_API_ENDPOINT")
EMP_API_TOKEN = os.getenv("EMP_API_TOKEN")

@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    headers = {
        "Authorization": f"Bearer {EMP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(base_url=EMP_API_ENDPOINT, headers=headers) as client:
        yield client

def print_curl_equivalent(method: str, payload: dict, sse: bool = False):
    """Print the curl equivalent of the HTTP request."""
    headers_str = (
        f"-H 'Authorization: Bearer {EMP_API_TOKEN}' "
        f"-H 'Content-Type: application/json'"
    )
    if sse:
        headers_str += " -H 'Accept: text/event-stream'"
    payload_str = json.dumps(payload)

    print(f"\n# Curl equivalent for {method} {EMP_API_ENDPOINT}:")
    print(f"curl -X {method} {EMP_API_ENDPOINT} \\\n     {headers_str} \\\n     -d '{payload_str}'\n")

@pytest.mark.asyncio
async def test_mcp_initialize(client: httpx.AsyncClient):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    print_curl_equivalent("POST", payload)

    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data

@pytest.mark.asyncio
async def test_mcp_tools_list(client: httpx.AsyncClient):
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    print_curl_equivalent("POST", payload)

    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]

    tools = data["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    assert "getallowedwebsite_account" in tool_names
    assert "eulerian_tool_invoke" in tool_names

@pytest.mark.asyncio
async def test_mcp_tool_call_json(client: httpx.AsyncClient):
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "eulerian_tool_invoke",
            "arguments": {
                "tool_name": "getallowedwebsite_account",
                "arguments": {}
            }
        }
    }
    print_curl_equivalent("POST", payload)

    response = await client.post("", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data

@pytest.mark.asyncio
async def test_mcp_tool_call_sse(client: httpx.AsyncClient):
    payload = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "eulerian_tool_invoke",
            "arguments": {
                "tool_name": "getallowedwebsite_account",
                "arguments": {}
            }
        }
    }
    print_curl_equivalent("POST", payload, sse=True)

    headers = {"Accept": "text/event-stream"}
    async with client.stream("POST", "", json=payload, headers=headers) as response:
        assert response.status_code == 200

        # Content-Type must be text/event-stream per SSE spec
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type, (
            f"Expected text/event-stream, got: {content_type}"
        )

        # Collect all SSE events
        events = []
        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk
            # SSE events are separated by double newlines
            while "\n\n" in buffer:
                event_block, buffer = buffer.split("\n\n", 1)
                for line in event_block.splitlines():
                    if line.startswith("data:"):
                        data = line[len("data:"):].strip()
                        if data and data != "[DONE]":
                            events.append(json.loads(data))

        assert len(events) > 0, "No SSE events received"

        # Each event must be a valid JSON-RPC envelope
        for event in events:
            assert event.get("jsonrpc") == "2.0", f"Missing jsonrpc field: {event}"
            assert "result" in event or "error" in event, (
                f"Event must have result or error: {event}"
            )

        # At least one event must carry the tool result
        results = [e for e in events if "result" in e and e.get("id") == 4]
        assert len(results) > 0, "No event matched request id=4"
        assert "content" in results[0]["result"], (
            f"Tool result must have content array: {results[0]}"
        )
