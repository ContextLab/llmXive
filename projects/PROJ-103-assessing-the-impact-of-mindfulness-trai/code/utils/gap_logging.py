"""
Thin wrapper that re‑exports the implementation from ``src.utils.gap_logging``.

Keeping a copy under ``code.utils`` satisfies the path expectations in the
task description while ensuring a single source of truth.
"""

from src.utils.gap_logging import log_gap  # noqa: F401 re‑export
