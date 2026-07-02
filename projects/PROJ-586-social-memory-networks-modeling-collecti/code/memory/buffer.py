"""Shared external memory buffer for the multi‑agent experiments.

The buffer stores arbitrary ``MemoryEntry`` objects and provides a very
lightweight API.  It is deliberately permissive – any unknown attribute
access returns a no‑op callable so that callers can safely use logging‑style
methods (e.g. ``info``/``debug``) without the buffer needing to implement
each one.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


@dataclass
class MemoryEntry:
    """A single entry stored in the shared memory buffer."""

    agent_id: int
    content: Any
    timestamp: float = field(default_factory=lambda: 0.0)


class MemoryBuffer:
    """Thread‑safe buffer that holds ``MemoryEntry`` objects."""

    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------- #
    # Core API used by the experiment code
    # ------------------------------------------------------------------- #
    def add(self, entry: MemoryEntry) -> None:
        """Append a new entry to the buffer."""
        with self._lock:
            self._entries.append(entry)

    def get_all(self) -> List[MemoryEntry]:
        """Return a shallow copy of all stored entries."""
        with self._lock:
            return list(self._entries)

    def reset(self) -> None:
        """Clear the buffer – used between independent simulation runs."""
        with self._lock:
            self._entries.clear()

    # ------------------------------------------------------------------- #
    # Compatibility shim – tolerate any unknown attribute/method.
    # ------------------------------------------------------------------- #
    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Return a no‑op callable for any attribute that does not exist.

        This makes the buffer compatible with logger‑style calls such as
        ``buffer.info(...)`` or ``buffer.custom_method(...)`` without raising
        ``AttributeError``.
        """

        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop


# Singleton instance used throughout the experiment scripts.
_SHARED_BUFFER: Optional[MemoryBuffer] = None


def get_shared_memory_buffer() -> MemoryBuffer:
    """Return the global shared memory buffer, creating it on first use."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER


def reset_shared_memory_buffer() -> None:
    """Convenient helper to clear the shared buffer."""
    get_shared_memory_buffer().reset()


# --------------------------------------------------------------------------- #
# Helper for parsing the special ``<MEMORY_ACTION>`` token that agents may emit.
# --------------------------------------------------------------------------- #

def parse_memory_action(token: str) -> Tuple[int, str]:
    """
    Expected token format: ``<MEMORY_ACTION:agent_id:action>``.
    Returns a tuple ``(agent_id, action)``.
    """
    try:
        prefix, payload = token.split(":", 1)
        if not prefix.startswith("<MEMORY_ACTION"):
            raise ValueError
        agent_part, action = payload.rstrip(">").split(":", 1)
        return int(agent_part), action
    except Exception as exc:
        raise ValueError(f"Invalid memory action token: {token}") from exc
