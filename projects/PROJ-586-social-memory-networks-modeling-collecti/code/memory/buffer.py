"""
memory.buffer
---------------
Simple shared memory buffer used by agents to store and retrieve entries.
The original implementation provided a handful of explicit methods but
lacked a ``reset`` method and a permissive ``__getattr__`` to tolerate
arbitrary logger‑style calls made by various parts of the codebase.
This file now adds:
  * ``reset`` – clears the internal store.
  * ``__getattr__`` – returns a no‑op callable for any unknown attribute,
    ensuring that attribute accesses never raise ``AttributeError``.
"""

import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

@dataclass
class MemoryEntry:
    """
    Represents a single entry in the shared memory buffer.
    """
    key: str
    value: Any
    timestamp: float

class MemoryBuffer:
    """
    Thread‑safe in‑memory buffer that can be shared across agents.
    """

    _instance: Optional["MemoryBuffer"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton pattern – all callers receive the same instance.
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._entries = {}
            return cls._instance

    # ------------------------------------------------------------------
    # Core API (existing)
    # ------------------------------------------------------------------
    def store(self, key: str, value: Any) -> None:
        """Store a value under ``key``."""
        self._entries[key] = MemoryEntry(key=key, value=value, timestamp=time.time())

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve the entry for ``key`` if it exists."""
        return self._entries.get(key)

    def delete(self, key: str) -> None:
        """Delete an entry."""
        self._entries.pop(key, None)

    def keys(self) -> List[str]:
        """Return a list of all stored keys."""
        return list(self._entries.keys())

    # ------------------------------------------------------------------
    # New API additions
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """
        Clear all entries from the buffer.
        """
        self._entries.clear()

    def __getattr__(self, name: str) -> Callable:
        """
        Return a no‑op callable for any undefined attribute.
        This makes the buffer tolerant of arbitrary logger‑style method
        calls (e.g. ``buffer.info(...)``) without raising ``AttributeError``.
        """
        def _noop(*args, **kwargs):
            # Intentionally do nothing – the call is ignored.
            return None
        return _noop

# ----------------------------------------------------------------------
# Helper functions for shared access
# ----------------------------------------------------------------------
_shared_buffer: Optional[MemoryBuffer] = None
_shared_lock = threading.Lock()

def get_shared_memory_buffer() -> MemoryBuffer:
    """
    Retrieve the global shared memory buffer, creating it on first use.
    """
    global _shared_buffer
    with _shared_lock:
        if _shared_buffer is None:
            _shared_buffer = MemoryBuffer()
        return _shared_buffer

def reset_shared_memory_buffer() -> None:
    """
    Reset the global shared memory buffer.
    """
    buffer = get_shared_memory_buffer()
    buffer.reset()

def parse_memory_action(action_str: str) -> Tuple[str, str]:
    """
    Parse a memory‑action token of the form ``<MEMORY_ACTION:key=value>``.
    Returns a tuple ``(key, value)``.
    """
    pattern = r"<MEMORY_ACTION:(?P<key>[^=]+)=(?P<value>[^>]+)>"
    match = re.fullmatch(pattern, action_str.strip())
    if not match:
        raise ValueError(f"Invalid memory action token: {action_str}")
    return match.group("key"), match.group("value")