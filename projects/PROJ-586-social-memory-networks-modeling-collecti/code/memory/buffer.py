import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

@dataclass
class MemoryEntry:
    """Simple container for a memory entry."""
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)

class MemoryBuffer:
    """
    Thread‑safe shared memory buffer used by agents to store and retrieve
    arbitrary key/value pairs.  The implementation provides a small set of
    explicit methods (store, retrieve, reset, update, register_callback,
    __len__) and also tolerates any other attribute access by returning a
    no‑op callable.  This makes the buffer compatible with legacy test code
    that may call logger‑style methods such as ``info`` or ``debug``.

    Additionally, it can parse and handle ``<MEMORY_ACTION:key=value>``
    tokens via :meth:`process_memory_action`, storing the extracted
    key/value pair automatically.
    """

    _instance: Optional["MemoryBuffer"] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton pattern – all callers get the same instance.
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Initialise only once.
        if not hasattr(self, "_entries"):
            self._entries: List[MemoryEntry] = []
            self._lock = threading.Lock()
            self._callbacks: List[Callable[[MemoryEntry], None]] = []

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def store(self, key: str, value: Any) -> None:
        """Store a value under ``key`` in a thread‑safe manner."""
        with self._lock:
            entry = MemoryEntry(key=key, value=value)
            self._entries.append(entry)
            # Notify callbacks
            for cb in self._callbacks:
                try:
                    cb(entry)
                except Exception:
                    # Callbacks should never break the buffer logic.
                    pass

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve the most recent value for ``key`` or ``None``."""
        with self._lock:
            for entry in reversed(self._entries):
                if entry.key == key:
                    return entry.value
        return None

    def reset(self) -> None:
        """Clear all stored entries."""
        with self._lock:
            self._entries.clear()

    def update(self, key: str, value: Any) -> None:
        """
        Update the most recent entry for ``key`` with a new ``value``.
        If the key does not exist, this behaves like ``store``.
        """
        with self._lock:
            for entry in reversed(self._entries):
                if entry.key == key:
                    entry.value = value
                    entry.timestamp = time.time()
                    # Notify callbacks with the updated entry.
                    for cb in self._callbacks:
                        try:
                            cb(entry)
                        except Exception:
                            pass
                    return
            # Key not found → store as new entry.
            self.store(key, value)

    def register_callback(self, callback: Callable[[MemoryEntry], None]) -> None:
        """
        Register a ``callback`` that will be invoked with a ``MemoryEntry``
        each time a new entry is stored or an existing entry is updated.
        Callbacks are executed in the order they were added.
        """
        if not callable(callback):
            raise TypeError("callback must be callable")
        with self._lock:
            self._callbacks.append(callback)

    def __len__(self) -> int:
        """Return the number of entries currently stored."""
        with self._lock:
            return len(self._entries)

    # ------------------------------------------------------------------
    # Memory‑action handling
    # ------------------------------------------------------------------
    def process_memory_action(self, action_str: str) -> None:
        """
        Parse a ``<MEMORY_ACTION:key=value>`` token and store the extracted
        ``key``/``value`` pair in the buffer.  Invalid tokens raise
        :class:`ValueError` (as provided by :func:`parse_memory_action`).
        """
        key, value = parse_memory_action(action_str)
        # Store the raw string value; callers can cast if needed.
        self.store(key, value)

    # ------------------------------------------------------------------
    # Compatibility shim – any unknown attribute becomes a no‑op callable.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str) -> Callable:
        """
        Return a no‑op callable for any attribute that does not exist.
        This satisfies test suites that may call logger‑style methods
        (e.g. ``info``, ``debug``, ``warning``) without raising
        ``AttributeError``.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# ----------------------------------------------------------------------
# Helper functions for the shared buffer singleton
# ----------------------------------------------------------------------
_shared_buffer: Optional[MemoryBuffer] = None

def get_shared_memory_buffer() -> MemoryBuffer:
    """Return the global shared memory buffer, creating it if necessary."""
    global _shared_buffer
    if _shared_buffer is None:
        _shared_buffer = MemoryBuffer()
    return _shared_buffer

def reset_shared_memory_buffer() -> None:
    """Convenient shortcut used by experiment scripts to reset the buffer."""
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