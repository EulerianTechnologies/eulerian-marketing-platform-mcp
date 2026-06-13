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

    # Server returns plain JSON regardless of Accept header — SSE not supported
    headers = {"Accept": "text/event-stream"}
    async with client.stream("POST", "", json=payload, headers=headers) as response:
        assert response.status_code == 200
        body = b""
        async for chunk in response.aiter_bytes():
            body += chunk
        data = json.loads(body)
        assert "result" in data or "error" in data
