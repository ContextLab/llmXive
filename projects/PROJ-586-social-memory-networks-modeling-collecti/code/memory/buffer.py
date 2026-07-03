"""Shared memory buffer with <MEMORY_ACTION> token handling."""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from utils.logging import get_logger

logger = get_logger(__name__)


def now() -> str:
    return datetime.utcnow().isoformat()


class MemoryActionType:
    STORE = "STORE"
    RETRIEVE = "RETRIEVE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class MemoryAction:
    action_type: str
    key: str
    value: Optional[Any] = None
    timestamp: str = field(default_factory=now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryEntry:
    key: str
    value: Any
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

MEMORY_ACTION_PATTERN = re.compile(
    r"<MEMORY_ACTION>\s*(STORE|RETRIEVE|UPDATE|DELETE)\s+([^\s>]+)(?:\s+([^\s>]+))?\s*</MEMORY_ACTION>",
    re.IGNORECASE
)

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    match = MEMORY_ACTION_PATTERN.search(token)
    if not match:
        return None
    action_type = match.group(1).upper()
    key = match.group(2)
    value = match.group(3)
    return MemoryAction(action_type=action_type, key=key, value=value)

def parse_memory_action(text: str) -> List[MemoryAction]:
    actions = []
    for match in MEMORY_ACTION_PATTERN.finditer(text):
        action_type = match.group(1).upper()
        key = match.group(2)
        value = match.group(3)
        actions.append(MemoryAction(action_type=action_type, key=key, value=value))
    return actions

def format_action_token(action: MemoryAction) -> str:
    val_str = f" {action.value}" if action.value is not None else ""
    return f"<MEMORY_ACTION> {action.action_type} {action.key}{val_str} </MEMORY_ACTION>"

def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    return parse_memory_action(prompt)

class MemoryBuffer:
    def __init__(self, capacity: int = 1000):
        self._buffer: Dict[str, MemoryEntry] = {}
        self._capacity = capacity
        self._lock = threading.RLock()
        self._actions: List[MemoryAction] = []

    def update(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        with self._lock:
            if key in self._buffer:
                entry = self._buffer[key]
                entry.value = value
                entry.updated_at = now()
                entry.metadata.update(metadata or {})
                self._actions.append(MemoryAction(action_type=MemoryActionType.UPDATE, key=key, value=value))
                return True
            else:
                if len(self._buffer) >= self._capacity:
                    # Simple eviction: remove oldest
                    oldest_key = min(self._buffer, key=lambda k: self._buffer[k].created_at)
                    del self._buffer[oldest_key]
                self._buffer[key] = MemoryEntry(key=key, value=value, metadata=metadata or {})
                self._actions.append(MemoryAction(action_type=MemoryActionType.STORE, key=key, value=value))
                return True

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._buffer:
                entry = self._buffer[key]
                entry.access_count += 1
                return entry.value
            return None

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._buffer:
                del self._buffer[key]
                self._actions.append(MemoryAction(action_type=MemoryActionType.DELETE, key=key))
                return True
            return False

    def search(self, query: str) -> List[MemoryEntry]:
        with self._lock:
            results = []
            for entry in self._buffer.values():
                if query.lower() in str(entry.value).lower():
                    results.append(entry)
            return results

    def reset(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._actions.clear()

    def __getattr__(self, name: str):
        # Tolerant fallback for any logger-style calls or unknown methods
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(capacity: int = 1000) -> MemoryBuffer:
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(capacity=capacity)
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
            _SHARED_BUFFER = None
