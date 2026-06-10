"""MCP server exposing llmXive librarian + claims tools (issue #295, item 2).

This package is named ``mcp_server`` (not ``mcp``) so it never shadows the
official MCP python SDK package. The SDK itself is an *optional* dependency
(``pip install llmxive[mcp]``) and is imported lazily inside
:func:`llmxive.mcp_server.server.create_server`, so ``import llmxive`` (and
``import llmxive.mcp_server``) stays light and works without the SDK.

Run a stdio server with::

    python -m llmxive.mcp_server
"""

from llmxive.mcp_server.server import create_server, main

__all__ = ["create_server", "main"]
