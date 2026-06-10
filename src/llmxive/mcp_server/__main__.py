"""Entry point: ``python -m llmxive.mcp_server`` runs a stdio MCP server."""

from __future__ import annotations

import sys


def _run() -> None:
    try:
        import mcp  # noqa: F401 — presence check for a clear install hint
    except ImportError:
        from llmxive.mcp_server.server import MISSING_MCP_SDK_MSG

        print(f"error: {MISSING_MCP_SDK_MSG}", file=sys.stderr)
        raise SystemExit(1) from None

    from llmxive.mcp_server import main

    main()


if __name__ == "__main__":
    _run()
