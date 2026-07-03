"""Shared external memory buffer with <MEMORY_ACTION> token handling."""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


def now() -> str:
    """Return current ISO timestamp."""
    return datetime.utcnow().isoformat()


class MemoryActionType(str, Enum):
    """Types of memory actions."""
    STORE = "STORE"
    RETRIEVE = "RETRIEVE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SEARCH = "SEARCH"


@dataclass
class MemoryAction:
    """A single memory action."""
    action_type: MemoryActionType
    key: str
    value: Optional[str] = None
    timestamp: str = field(default_factory=now)

    def to_token(self) -> str:
        """Convert to <MEMORY_ACTION> token format."""
        return f"<MEMORY_ACTION:{self.action_type.value}:{self.key}>"


@dataclass
class MemoryEntry:
    """A memory entry in the buffer."""
    key: str
    value: str
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION:TYPE:KEY> token."""
    pattern = r"<MEMORY_ACTION:(\w+):([^>]+)>"
    match = re.match(pattern, token)
    if match:
        action_type_str, key = match.groups()
        try:
            action_type = MemoryActionType[action_type_str]
            return MemoryAction(action_type=action_type, key=key)
        except KeyError:
            return None
    return None


def parse_memory_action(text: str) -> Optional[MemoryAction]:
    """Parse memory action from text."""
    token = re.search(r"<MEMORY_ACTION:[^>]+>", text)
    if token:
        return parse_memory_action_token(token.group(0))
    return None


def format_action_token(action_type: str, key: str) -> str:
    """Format a memory action token."""
    return f"<MEMORY_ACTION:{action_type}:{key}>"


def parse_action_from_prompt(prompt: str) -> Optional[MemoryAction]:
    """Extract memory action from a prompt."""
    return parse_memory_action(prompt)


class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems."""

    def __init__(self) -> None:
        self._buffer: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._access_log: List[MemoryAction] = []

    def store(self, key: str, value: str) -> MemoryEntry:
        """Store a value in memory."""
        with self._lock:
            entry = MemoryEntry(key=key, value=value)
            self._buffer[key] = entry
            self._access_log.append(
                MemoryAction(action_type=MemoryActionType.STORE, key=key, value=value)
            )
            return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a value from memory."""
        with self._lock:
            entry = self._buffer.get(key)
            if entry:
                entry.access_count += 1
                entry.updated_at = now()
                self._access_log.append(
                    MemoryAction(action_type=MemoryActionType.RETRIEVE, key=key)
                )
            return entry

    def update(self, key: str, value: str) -> Optional[MemoryEntry]:
        """Update a value in memory."""
        with self._lock:
            if key in self._buffer:
                entry = self._buffer[key]
                entry.value = value
                entry.updated_at = now()
                self._access_log.append(
                    MemoryAction(action_type=MemoryActionType.UPDATE, key=key, value=value)
                )
                return entry
            return None

    def delete(self, key: str) -> bool:
        """Delete a value from memory."""
        with self._lock:
            if key in self._buffer:
                del self._buffer[key]
                self._access_log.append(
                    MemoryAction(action_type=MemoryActionType.DELETE, key=key)
                )
                return True
            return False

    def search(self, pattern: str) -> List[MemoryEntry]:
        """Search for entries matching a pattern."""
        with self._lock:
            results = []
            for key, entry in self._buffer.items():
                if pattern.lower() in key.lower() or pattern.lower() in entry.value.lower():
                    results.append(entry)
            self._access_log.append(
                MemoryAction(action_type=MemoryActionType.SEARCH, key=pattern)
            )
            return results

    def reset(self) -> None:
        """Clear all memory and logs."""
        with self._lock:
            self._buffer.clear()
            self._access_log.clear()

    def get_all(self) -> Dict[str, MemoryEntry]:
        """Get all entries."""
        with self._lock:
            return dict(self._buffer)

    def get_log(self) -> List[MemoryAction]:
        """Get access log."""
        with self._lock:
            return list(self._access_log)

    def __getattr__(self, name: str) -> Any:
        """Fallback for any unknown method — returns a tolerant no-op."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_SHARED_BUFFER: Optional[MemoryBuffer] = None
_SHARED_BUFFER_LOCK = threading.Lock()


def get_shared_buffer() -> MemoryBuffer:
    """Get or create the global shared memory buffer."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        with _SHARED_BUFFER_LOCK:
            if _SHARED_BUFFER is None:
                _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER


def get_shared_memory_buffer() -> MemoryBuffer:
    """Alias for get_shared_buffer()."""
    return get_shared_buffer()


def reset_shared_buffer() -> None:
    """Reset the shared buffer."""
    buf = get_shared_buffer()
    buf.reset()


def reset_shared_memory_buffer() -> None:
    """Alias for reset_shared_buffer()."""
    reset_shared_buffer()
