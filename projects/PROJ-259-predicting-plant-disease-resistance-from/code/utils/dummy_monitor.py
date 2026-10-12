"""
Dummy resource monitor stub.

This module provides a minimal no‑op context manager used as a placeholder
for the real resource‑monitor implementation that will be added later
(see tasks T046, T066). It satisfies the verification requirement that
importing ``dummy_monitor`` and invoking its context manager does not raise
any exception.

The public API mirrors the expected usage pattern in the rest of the
codebase: a ``DummyMonitor`` class that can be used directly as a context
manager, and a convenience ``monitor`` factory function that returns an
instance of ``DummyMonitor``.
"""

from __future__ import annotations
from typing import Any, Optional

class DummyMonitor:
    """
    No‑op resource monitor.

    Parameters are accepted for compatibility but ignored.
    """

    def __init__(self, stage_name: Optional[str] = None, *args: Any, **kwargs: Any) -> None:
        self.stage_name = stage_name or "unnamed_stage"

    def __enter__(self) -> "DummyMonitor":
        # No setup required.
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> bool:
        # Nothing to clean up. Propagate any exception.
        return False

def monitor(stage_name: Optional[str] = None, *args: Any, **kwargs: Any) -> DummyMonitor:
    """
    Convenience factory returning a ``DummyMonitor`` instance.

    Example
    -------
    >>> from dummy_monitor import monitor
    >>> with monitor("preprocess"):
    ...     pass  # no‑op
    """
    return DummyMonitor(stage_name=stage_name, *args, **kwargs)