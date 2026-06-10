"""Real-call: llmXive MCP server over stdio (issue #295, scope item 2).

Spawns ``python -m llmxive.mcp_server`` as a real subprocess and drives it
with the official MCP SDK client — real transport, real network calls, no
mocks. Gated by LLMXIVE_REAL_TESTS=1 (tests/conftest.py); the arXiv search
is additionally marked ``slow`` (rate-limited external API, ~seconds-to-
minutes under backoff) so it runs in the nightly suite, not the PR gate.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import pytest

pytest.importorskip("mcp", reason="optional extra not installed: pip install llmxive[mcp]")

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llmxive.credentials import load_dartmouth_key

_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable, args=["-m", "llmxive.mcp_server"]
)


def _call_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Spawn the stdio server, call one tool, return the decoded payload."""

    async def _go() -> Any:
        async with stdio_client(_SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                assert not result.isError, f"tool {name} errored: {result.content}"
                if result.structuredContent is not None:
                    structured = result.structuredContent
                    # FastMCP wraps non-dict returns as {"result": ...}.
                    if isinstance(structured, dict) and set(structured) == {"result"}:
                        return structured["result"]
                    return structured
                # Fall back to the text content (JSON-encoded by FastMCP).
                texts = [c.text for c in result.content if hasattr(c, "text")]
                assert texts, f"tool {name} returned no content"
                return json.loads(texts[0])

    return anyio.run(_go)


@pytest.mark.slow
def test_search_arxiv_over_stdio_returns_real_results() -> None:
    payload = _call_tool(
        "search_arxiv", {"query": "knot theory crossing number", "max_results": 2}
    )
    assert isinstance(payload, list), f"expected list of candidates, got {payload!r}"
    assert len(payload) >= 1
    first = payload[0]
    assert first.get("backend") == "arxiv"
    assert first.get("title"), f"first result has no title: {first!r}"
    assert first.get("id"), f"first result has no arXiv id: {first!r}"


@pytest.mark.skipif(
    not load_dartmouth_key(),
    reason="Dartmouth Chat API key unavailable (env + credentials.toml)",
)
def test_credit_balance_over_stdio() -> None:
    payload = _call_tool("credit_balance", {})
    assert isinstance(payload, dict), f"expected dict, got {payload!r}"
    assert "error" not in payload, f"credit_balance failed: {payload}"
    assert payload["max_budget"] > 0
    assert {"account", "spend", "budget_duration", "budget_reset_at", "remaining"} <= set(
        payload
    )
