from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Any, List

@dataclass(frozen=True)
class MemoryAction:
    """Simple representation of a memory action token."""
    token: str

def parse_memory_action(text: str) -> MemoryAction:
    """Parse a string into a MemoryAction. Very permissive."""
    token = text.strip()
    return MemoryAction(token=token)

class MemoryBuffer:
    """Thread‑safe in‑memory buffer for storing memory actions."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any):
        # Singleton pattern – all callers share the same buffer
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_internal()
            return cls._instance

    def _init_internal(self) -> None:
        self._entries: List[MemoryAction] = []
        self._buffer_lock = threading.Lock()

    # Core API -----------------------------------------------------------------
    def add(self, action: MemoryAction) -> None:
        """Add a MemoryAction to the buffer."""
        with self._buffer_lock:
            self._entries.append(action)

    def get_all(self) -> List[MemoryAction]:
        """Return a copy of all stored actions."""
        with self._buffer_lock:
            return list(self._entries)

    def reset(self) -> None:
        """Clear the buffer – required by several unit tests."""
        with self._buffer_lock:
            self._entries.clear()

    # Tolerant fallback ---------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Any attribute that is not explicitly defined becomes a no‑op callable.
        This satisfies callers that treat the buffer like a logger (e.g. .info(),
        .debug(), .warning()) without raising AttributeError.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

def get_shared_memory_buffer() -> MemoryBuffer:
    """Factory returning the singleton buffer."""
    return MemoryBuffer()
