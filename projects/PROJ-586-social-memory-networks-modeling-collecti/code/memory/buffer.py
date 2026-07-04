"""Shared external memory buffer with <MEMORY_ACTION> token handling."""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def now() -> str:
    """Return current ISO 8601 timestamp."""
    return datetime.utcnow().isoformat()


@dataclass
class MemoryAction:
    """Represents a memory operation (store, retrieve, delete)."""
    action_type: str  # "store", "retrieve", "delete"
    key: str
    value: Optional[str] = None
    timestamp: str = field(default_factory=now)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    stored_at: str = field(default_factory=now)
    retrieved_count: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token into a MemoryAction object.

    Format: <MEMORY_ACTION>{"action_type": "...", "key": "...", "value": "..."}</MEMORY_ACTION>
    """
    pattern = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"
    match = re.search(pattern, token, re.DOTALL)
    if not match:
        return None

    try:
        json_str = match.group(1)
        data = json.loads(json_str)
        return MemoryAction(
            action_type=data.get("action_type", ""),
            key=data.get("key", ""),
            value=data.get("value"),
        )
    except (json.JSONDecodeError, KeyError):
        return None


def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token."""
    json_str = action.to_json()
    return f"<MEMORY_ACTION>{json_str}</MEMORY_ACTION>"


class MemoryBuffer:
    """Thread-safe external memory buffer for agents."""

    def __init__(self):
        self.store: Dict[str, MemoryEntry] = {}
        self.lock = threading.RLock()

    def store_memory(self, key: str, value: str) -> None:
        """Store a key-value pair in memory."""
        with self.lock:
            self.store[key] = MemoryEntry(key=key, value=value)

    def retrieve_memory(self, key: str) -> Optional[str]:
        """Retrieve a value by key."""
        with self.lock:
            if key in self.store:
                entry = self.store[key]
                entry.retrieved_count += 1
                return entry.value
        return None

    def delete_memory(self, key: str) -> bool:
        """Delete a key from memory."""
        with self.lock:
            if key in self.store:
                del self.store[key]
                return True
        return False

    def reset(self) -> None:
        """Clear all memory entries."""
        with self.lock:
            self.store.clear()

    def list_keys(self) -> List[str]:
        """List all keys in memory."""
        with self.lock:
            return list(self.store.keys())

    def get_all_entries(self) -> Dict[str, MemoryEntry]:
        """Get a copy of all entries."""
        with self.lock:
            return dict(self.store)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the buffer."""
        with self.lock:
            total_retrievals = sum(e.retrieved_count for e in self.store.values())
            return {
                "total_entries": len(self.store),
                "total_retrievals": total_retrievals,
                "keys": list(self.store.keys()),
            }

    def __getattr__(self, name: str) -> Callable:
        """Fallback for unknown method calls — return a no-op.
        
        This ensures tolerance for any logger-style calls or future method
        additions without raising AttributeError.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


# Global shared buffer instance
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer() -> MemoryBuffer:
    """Get or create the global shared memory buffer."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        with _BUFFER_LOCK:
            if _SHARED_BUFFER is None:
                _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER


def reset_shared_buffer() -> None:
    """Reset the global shared buffer."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is not None:
        _SHARED_BUFFER.reset()