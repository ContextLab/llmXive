"""Unit: llmXive MCP server registers exactly the expected tools (issue #295).

Skips cleanly when the optional ``mcp`` extra is not installed. No mocks —
this introspects the real FastMCP server object via the SDK's own
``list_tools()`` API.
"""

from __future__ import annotations

import pytest

mcp = pytest.importorskip("mcp", reason="optional extra not installed: pip install llmxive[mcp]")

import anyio  # noqa: E402

EXPECTED_TOOLS = {
    "search_semantic_scholar",
    "search_arxiv",
    "get_arxiv_paper",
    "search_theorems",
    "resolve_reference",
    "register_and_resolve_claims",
    "claim_status",
    "credit_balance",
}


def test_server_lists_exactly_the_expected_tools() -> None:
    from llmxive.mcp_server import create_server

    server = create_server()
    assert server.name == "llmxive"

    async def _list() -> list:
        return await server.list_tools()

    tools = anyio.run(_list)
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS

    for tool in tools:
        assert tool.description and tool.description.strip(), (
            f"tool {tool.name} has an empty description"
        )


def test_import_llmxive_mcp_server_does_not_require_running_server() -> None:
    """The package imports light: create_server is the only SDK touchpoint."""
    import llmxive.mcp_server as pkg

    assert callable(pkg.create_server)
    assert callable(pkg.main)
