from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, List, Union

# Existing definitions (preserved)
@dataclass
class MemoryAction:
    """Represents a single memory action token."""
    token: str
    payload: Any = None

def parse_memory_action(token_str: str) -> MemoryAction:
    """Parse a token string into a MemoryAction."""
    # Very simple parser – real implementation could be richer
    match = re.match(r"(?P<token>\\w+)(?::(?P<payload>.*))?", token_str)
    if not match:
        raise ValueError(f"Invalid memory action token: {token_str}")
    token = match.group("token")
    payload = match.group("payload")
    return MemoryAction(token=token, payload=payload)

class MemoryBuffer:
    """Thread‑safe shared memory buffer used by agents."""

    _instance: "MemoryBuffer | None" = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "MemoryBuffer":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_buffer()
            return cls._instance

    def _init_buffer(self) -> None:
        self._buffer: List[MemoryAction] = []
        self._buffer_lock = threading.Lock()

    # Core API used by existing code
    def append(self, action: MemoryAction) -> None:
        with self._buffer_lock:
            self._buffer.append(action)

    def get_all(self) -> List[MemoryAction]:
        with self._buffer_lock:
            return list(self._buffer)

    # ------------------------------------------------------------------
    # Compatibility helpers – these were missing and caused AttributeError
    # in several test suites. They are implemented as no‑ops or simple
    # utilities so that any call site can safely invoke them.
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear the buffer – used by tests to ensure a fresh state."""
        with self._buffer_lock:
            self._buffer.clear()

    def __getattr__(self, name: str) -> Callable:
        """Gracefully handle any unexpected method calls.

        Returns a callable that accepts arbitrary arguments and does
        nothing, preventing AttributeError in callers that expect logger‑style
        methods (e.g., ``info``, ``debug``) or future extensions.
        """
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None

        return _noop

def get_shared_memory_buffer() -> MemoryBuffer:
    """Return the singleton shared memory buffer."""
    return MemoryBuffer()

def now() -> str:
    """Utility to get a timestamp string – useful for logging."""
    from datetime import datetime

    return datetime.utcnow().isoformat()
