"""llmxive.fill — authoritative-fill / claim auto-correction (spec 017).

Public surface
--------------
fill_claim  — top-level orchestrator (from fill.service once implemented).

This module is a lazy re-export so downstream importers can write::

    from llmxive.fill import fill_claim

without pulling in all channel/HTTP dependencies at import time.
"""

from __future__ import annotations


def __getattr__(name: str):  # noqa: ANN001
    if name == "fill_claim":
        from llmxive.fill import service  # noqa: PLC0415

        return service.fill_claim
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["fill_claim"]
