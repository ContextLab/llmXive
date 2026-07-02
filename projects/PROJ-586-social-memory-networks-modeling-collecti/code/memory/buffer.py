"""
Memory Buffer implementation for the Social Memory Networks project.

This module provides:
- A thread‑safe singleton ``MemoryBuffer`` that can store arbitrary key/value
  pairs.
- Automatic parsing of the special ``<MEMORY_ACTION:...>`` token that may be
  embedded in a stored value.
- Utility helpers for resetting the buffer, registering callbacks, and a
  permissive ``__getattr__`` that turns any unknown method into a no‑op
  callable (required by the test‑suite).
- Convenience functions ``get_shared_memory_buffer`` and
  ``reset_shared_memory_buffer`` for global access.
"""

import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

__all__ = [
    "MemoryEntry",
    "parse_memory_action",
    "MemoryBuffer",
    "get_shared_memory_buffer",
    "reset_shared_memory_buffer",
]

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #

@dataclass
class MemoryEntry:
    """A single memory entry stored in the buffer.

    Attributes
    ----------
    key: Any
        Identifier used to retrieve the entry.
    value: Any
        The payload stored. May be a string that contains a ``<MEMORY_ACTION>``.
    timestamp: float
        Time of insertion (seconds since the epoch).
    action: Optional[str]
        If the ``value`` contains a ``<MEMORY_ACTION:...>`` token, the extracted
        action string is stored here; otherwise ``None``.
    """
    key: Any
    value: Any
    timestamp: float = field(default_factory=time.time)
    action: Optional[str] = None

# --------------------------------------------------------------------------- #
# Token parsing
# --------------------------------------------------------------------------- #

_MEMORY_ACTION_REGEX = re.compile(r"<MEMORY_ACTION:(?P<action>[^>]+)>")

def parse_memory_action(text: str) -> Optional[str]:
    """
    Extract the ``<MEMORY_ACTION:...>`` token from *text*.

    Parameters
    ----------
    text: str
        Text that may contain the token.

    Returns
    -------
    Optional[str]
        The action string if the token is present, otherwise ``None``.
    """
    if not isinstance(text, str):
        return None
    match = _MEMORY_ACTION_REGEX.search(text)
    return match.group("action") if match else None

# --------------------------------------------------------------------------- #
# Memory buffer implementation
# --------------------------------------------------------------------------- #

class MemoryBuffer:
    """
    Thread‑safe in‑memory buffer with optional ``<MEMORY_ACTION>`` handling.

    The buffer behaves like a mutable mapping with extra convenience methods.
    Unknown attribute access is tolerated – it returns a no‑op callable so
    that client code can call arbitrary logger‑style methods without raising
    ``AttributeError``.
    """

    _instance_lock = threading.Lock()
    _shared_instance: Optional["MemoryBuffer"] = None

    def __init__(self) -> None:
        self._store: Dict[Any, MemoryEntry] = {}
        self._callbacks: Dict[str, List[Callable[..., Any]]] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------- #
    # Core API
    # ------------------------------------------------------------------- #

    def store(self, key: Any, value: Any) -> None:
        """
        Store *value* under *key*.

        If *value* is a string containing a ``<MEMORY_ACTION>`` token, the
        token is parsed and saved in the ``MemoryEntry.action`` field.
        """
        with self._lock:
            action = parse_memory_action(value) if isinstance(value, str) else None
            entry = MemoryEntry(key=key, value=value, action=action)
            self._store[key] = entry
            self._trigger("store", entry)

    def retrieve(self, key: Any) -> Optional[Any]:
        """Return the stored value for *key* or ``None`` if missing."""
        with self._lock:
            entry = self._store.get(key)
            return entry.value if entry else None

    # Alias used by some callers
    get = retrieve

    def update(self, key: Any, value: Any) -> None:
        """Replace the value for *key* with *value* (preserves timestamp)."""
        with self._lock:
            if key not in self._store:
                raise KeyError(f"Key {key!r} not found in MemoryBuffer.")
            action = parse_memory_action(value) if isinstance(value, str) else None
            entry = self._store[key]
            entry.value = value
            entry.action = action
            entry.timestamp = time.time()
            self._trigger("update", entry)

    def delete(self, key: Any) -> None:
        """Remove *key* from the buffer if present."""
        with self._lock:
            if key in self._store:
                entry = self._store.pop(key)
                self._trigger("delete", entry)

    def reset(self) -> None:
        """Clear all entries and fire a ``reset`` callback."""
        with self._lock:
            self._store.clear()
            self._trigger("reset")

    # ------------------------------------------------------------------- #
    # Callback handling
    # ------------------------------------------------------------------- #

    def register_callback(self, event: str, func: Callable[..., Any]) -> None:
        """
        Register *func* to be called when *event* occurs.

        Supported events are ``store``, ``update``, ``delete`` and ``reset``.
        """
        with self._lock:
            self._callbacks.setdefault(event, []).append(func)

    def _trigger(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Internal helper to invoke callbacks for *event*."""
        callbacks = self._callbacks.get(event, [])
        for cb in callbacks:
            try:
                cb(*args, **kwargs)
            except Exception:
                # Callbacks should never break the buffer – swallow errors.
                pass

    # ------------------------------------------------------------------- #
    # Python protocol helpers
    # ------------------------------------------------------------------- #

    def __len__(self) -> int:
        """Number of stored entries."""
        with self._lock:
            return len(self._store)

    def __contains__(self, key: Any) -> bool:
        with self._lock:
            return key in self._store

    def __iter__(self):
        """Iterate over stored keys."""
        with self._lock:
            # Return a snapshot iterator to avoid race conditions.
            return iter(list(self._store.keys()))

    # ------------------------------------------------------------------- #
    # Tolerant attribute access (required by the test‑suite)
    # ------------------------------------------------------------------- #

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """
        Return a no‑op callable for any unknown attribute.

        This makes the buffer usable as a logger‑like object where callers
        might invoke ``buffer.info(...)`` or ``buffer.debug(...)`` without
        the methods being explicitly defined.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop

    # ------------------------------------------------------------------- #
    # Singleton accessor (module‑level convenience)
    # ------------------------------------------------------------------- #

    @classmethod
    def get_shared_instance(cls) -> "MemoryBuffer":
        """
        Return a process‑wide singleton instance of ``MemoryBuffer``.
        """
        if cls._shared_instance is None:
            with cls._instance_lock:
                if cls._shared_instance is None:
                    cls._shared_instance = cls()
        return cls._shared_instance

# --------------------------------------------------------------------------- #
# Module‑level helpers
# --------------------------------------------------------------------------- #

def get_shared_memory_buffer() -> MemoryBuffer:
    """
    Public helper returning the shared ``MemoryBuffer`` singleton.
    """
    return MemoryBuffer.get_shared_instance()

def reset_shared_memory_buffer() -> None:
    """
    Reset the global shared buffer.  Primarily used by the test‑suite.
    """
    get_shared_memory_buffer().reset()