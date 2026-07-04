"""Shared memory buffer with token handling."""
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
    action: str  # 'add', 'delete', 'query'
    content: str
    timestamp: str = field(default_factory=now)


@dataclass
class MemoryEntry:
    id: int
    action: MemoryAction
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=now)


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token."""
    pattern = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"
    match = re.search(pattern, token)
    if match:
        try:
            data = json.loads(match.group(1))
            return MemoryAction(
                action=data.get("action", "add"),
                content=data.get("content", "")
            )
        except json.JSONDecodeError:
            return None
    return None


def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction to a token string."""
    data = asdict(action)
    return f"<MEMORY_ACTION>{json.dumps(data)}</MEMORY_ACTION>"


class MemoryBuffer:
    """Thread-safe shared memory buffer."""
    
    _instance: Optional["MemoryBuffer"] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._entries: List[MemoryEntry] = []
        self._next_id = 0
        self._lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def update(self, content: str, action_type: str = "add") -> MemoryEntry:
        with self._lock:
            action = MemoryAction(action=action_type, content=content)
            entry = MemoryEntry(id=self._next_id, action=action)
            self._entries.append(entry)
            self._next_id += 1
            return entry
    
    def delete(self, entry_id: int) -> bool:
        with self._lock:
            for i, entry in enumerate(self._entries):
                if entry.id == entry_id:
                    del self._entries[i]
                    return True
            return False
    
    def query(self, query_text: str) -> List[MemoryEntry]:
        # Simple substring search for simulation
        with self._lock:
            return [e for e in self._entries if query_text in e.action.content]
    
    def reset(self):
        """Reset the buffer."""
        with self._lock:
            self._entries.clear()
            self._next_id = 0
    
    def __getattr__(self, name: str):
        # Tolerant fallback for unknown logger-style calls
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_SHARED_BUFFER: Optional[MemoryBuffer] = None


def get_shared_buffer() -> MemoryBuffer:
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER


def reset_shared_buffer():
    global _SHARED_BUFFER
    if _SHARED_BUFFER:
        _SHARED_BUFFER.reset()
        _SHARED_BUFFER = None
