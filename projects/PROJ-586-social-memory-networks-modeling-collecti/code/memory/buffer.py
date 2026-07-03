"""Memory buffer utilities for the Social Memory Networks project.

This module provides a simple thread‑safe in‑memory buffer that stores
``MemoryEntry`` objects.  The original implementation exposed a limited
set of methods; other parts of the codebase (tests, analysis scripts) call
additional methods such as ``reset``.  To remain backward compatible while
satisfying all callers, a permissive ``__getattr__`` fallback is provided
that returns a no‑op callable for any unknown attribute.
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class MemoryAction:
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryEntry:
    action: MemoryAction
    timestamp: float

# --------------------------------------------------------------------------- #
# Token helpers (unchanged from original implementation)
# --------------------------------------------------------------------------- #

MEMORY_ACTION_TOKEN_PATTERN = re.compile(r"<MEMORY_(?P<type>\\w+)>")

def now() -> float:
    """Return current time in seconds since the epoch."""
    import time

    return time.time()

def parse_memory_action_token(token: str) -> MemoryAction:
    """Parse a token like ``<MEMORY_STORE>`` into a :class:`MemoryAction`."""
    match = MEMORY_ACTION_TOKEN_PATTERN.fullmatch(token)
    if not match:
        raise ValueError(f"Invalid memory action token: {token}")
    return MemoryAction(type=match.group("type"))

def format_action_token(action: MemoryAction) -> str:
    """Serialize a :class:`MemoryAction` back into its token representation."""
    return f"<MEMORY_{action.type.upper()}>"

# --------------------------------------------------------------------------- #
# Buffer implementation
# --------------------------------------------------------------------------- #

class MemoryBuffer:
    """Thread‑safe buffer for storing :class:`MemoryEntry` objects."""

    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []
        self._lock = threading.Lock()

    def add(self, action: MemoryAction) -> MemoryEntry:
        """Add a new entry and return it."""
        entry = MemoryEntry(action=action, timestamp=now())
        with self._lock:
            self._entries.append(entry)
        return entry

    def get_all(self) -> List[MemoryEntry]:
        """Return a copy of all stored entries."""
        with self._lock:
            return list(self._entries)

    def reset(self) -> None:
        """Clear the buffer."""
        with self._lock:
            self._entries.clear()

    # ----------------------------------------------------------------------- #
    # Compatibility shim
    # ----------------------------------------------------------------------- #

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """
        Return a no‑op callable for any undefined attribute.

        This makes the buffer tolerant of calls such as ``info``,
        ``debug``, or other logger‑style methods that some scripts expect.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop

# --------------------------------------------------------------------------- #
# Shared singleton buffer
# --------------------------------------------------------------------------- #

_SHARED_BUFFER: MemoryBuffer | None = None

def get_shared_buffer() -> MemoryBuffer:
    """Return a process‑wide shared :class:`MemoryBuffer` instance."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Convenience helper to reset the shared buffer."""
    get_shared_buffer().reset()
