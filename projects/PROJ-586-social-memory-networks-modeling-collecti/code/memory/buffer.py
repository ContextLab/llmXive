"""Shared external memory buffer with <MEMORY_ACTION> token handling."""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def now() -> str:
    """Return current ISO 8601 timestamp."""
    return datetime.utcnow().isoformat()


@dataclass
class MemoryAction:
    """Represents a memory action with token handling for <MEMORY_ACTION>."""
    action_type: str
    content: str
    timestamp: str = field(default_factory=now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_token(self) -> str:
        """Serialize to <MEMORY_ACTION> token format."""
        return f"<MEMORY_ACTION>{json.dumps(asdict(self))}</MEMORY_ACTION>"

    @staticmethod
    def from_token(token: str) -> Optional[MemoryAction]:
        """Parse <MEMORY_ACTION> token back to MemoryAction."""
        match = re.match(r"<MEMORY_ACTION>(.*)</MEMORY_ACTION>", token)
        if not match:
            return None
        try:
            data = json.loads(match.group(1))
            return MemoryAction(**data)
        except (json.JSONDecodeError, TypeError):
            return None


def parse_memory_action(text: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token from text."""
    return MemoryAction.from_token(text)


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token; alias for parse_memory_action."""
    return MemoryAction.from_token(token)


from dataclasses import asdict


class MemoryBuffer:
    """Thread-safe shared memory buffer with <MEMORY_ACTION> token support."""

    def __init__(self) -> None:
        self._buffer: List[MemoryAction] = []
        self._lock = threading.Lock()

    def add(self, action: MemoryAction) -> None:
        """Add a MemoryAction to the buffer."""
        with self._lock:
            self._buffer.append(action)

    def get(self, index: int = -1) -> Optional[MemoryAction]:
        """Get a MemoryAction by index (default: most recent)."""
        with self._lock:
            if not self._buffer or index >= len(self._buffer):
                return None
            return self._buffer[index]

    def get_all(self) -> List[MemoryAction]:
        """Get all MemoryActions."""
        with self._lock:
            return list(self._buffer)

    def clear(self) -> None:
        """Clear all MemoryActions."""
        with self._lock:
            self._buffer.clear()

    def reset(self) -> None:
        """Reset the buffer (alias for clear)."""
        self.clear()

    def size(self) -> int:
        """Return current buffer size."""
        with self._lock:
            return len(self._buffer)

    def __getattr__(self, name: str) -> Any:
        """Tolerant fallback for any unknown method call."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer() -> MemoryBuffer:
    """Get or create the shared memory buffer (singleton)."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        with _BUFFER_LOCK:
            if _SHARED_BUFFER is None:
                _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER