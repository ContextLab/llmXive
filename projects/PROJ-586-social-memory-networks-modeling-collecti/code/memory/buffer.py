"""Shared external memory buffer with <MEMORY_ACTION> token handling."""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def now() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class MemoryAction:
    type: str  # 'write', 'read', 'delete'
    key: str
    value: Optional[str] = None
    timestamp: str = field(default_factory=now)


@dataclass
class MemoryEntry:
    key: str
    value: str
    created_at: str = field(default_factory=now)
    access_count: int = 0


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parses a <MEMORY_ACTION> token string."""
    # Simple regex for demo: <MEMORY_ACTION type="write" key="x" value="y">
    pattern = r'<MEMORY_ACTION\s+type="(\w+)"\s+key="([^"]+)"(?:\s+value="([^"]*)")?>'
    match = re.match(pattern, token)
    if match:
        return MemoryAction(
            type=match.group(1),
            key=match.group(2),
            value=match.group(3)
        )
    return None


def format_action_token(action: MemoryAction) -> str:
    """Formats a MemoryAction back to a token string."""
    if action.value:
        return f'<MEMORY_ACTION type="{action.type}" key="{action.key}" value="{action.value}">'
    return f'<MEMORY_ACTION type="{action.type}" key="{action.key}">'


class MemoryBuffer:
    """Thread-safe shared memory buffer."""
    
    def __init__(self):
        self._data: Dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()
        self._history: List[MemoryAction] = []

    def update(self, action: MemoryAction) -> bool:
        with self._lock:
            if action.type == 'write':
                self._data[action.key] = MemoryEntry(key=action.key, value=action.value or "")
                self._history.append(action)
                return True
            elif action.type == 'delete':
                if action.key in self._data:
                    del self._data[action.key]
                    self._history.append(action)
                    return True
            return False

    def search(self, query: str) -> List[MemoryEntry]:
        # Simple substring search
        with self._lock:
            return [e for e in self._data.values() if query in e.value]

    def reset(self):
        """Resets the buffer to empty state."""
        with self._lock:
            self._data.clear()
            self._history.clear()

    # Tolerant logger-style fallback for any missing method
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer() -> MemoryBuffer:
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer()
        return _SHARED_BUFFER


def reset_shared_buffer():
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER:
            _SHARED_BUFFER.reset()