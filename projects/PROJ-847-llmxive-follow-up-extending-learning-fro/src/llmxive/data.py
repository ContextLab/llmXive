"""Legacy wrapper for ``code.data``.

Provides the same public API expected by the original quick‑start
commands (e.g. ``python -m src.llmxive.data --download``).
"""
from __future__ import annotations

# Re‑export the implementation from the new location.
from code.data import (
    load_gsm8k,
    load_bigbench_lite,
    download_all,
    main,
)

__all__ = [
    "load_gsm8k",
    "load_bigbench_lite",
    "download_all",
    "main",
]
