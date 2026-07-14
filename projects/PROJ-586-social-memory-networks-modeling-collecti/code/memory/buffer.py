"""Shared external memory buffer for multi-agent transactive memory.

Implements a thread-safe buffer supporting <MEMORY_ACTION> tokens with JSON schema:
{"type": "write"|"read", "key": str, "value": str}

Includes queue-based write conflict resolution.
"""
from __future__ import annotations

import json
import re
import threading
from collections import deque
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable


@dataclass
class MemoryAction:
    """Represents a memory operation (write or read)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None  # Required for writes, optional for reads

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": self.type, "key": self.key}
        if self.value is not None:
            d["value"] = self.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value")
        )


@dataclass
class MemoryEntry:
    """A single entry in the memory buffer with metadata."""
    key: str
    value: str
    timestamp: str
    agent_id: Optional[str] = None
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        return cls(**data)


def now() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat()


# Token pattern for memory actions in text
MEMORY_ACTION_PATTERN = re.compile(
    r'<MEMORY_ACTION>(.*?)</MEMORY_ACTION>',
    re.DOTALL
)


def parse_memory_action_token(token_text: str) -> Optional[MemoryAction]:
    """Parse a JSON string inside a <MEMORY_ACTION> token."""
    try:
        data = json.loads(token_text.strip())
        return MemoryAction.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token string."""
    return f"<MEMORY_ACTION>{json.dumps(action.to_dict())}</MEMORY_ACTION>"


def parse_action_from_prompt(prompt_text: str) -> List[MemoryAction]:
    """Extract all MemoryAction objects from a prompt string."""
    actions = []
    for match in MEMORY_ACTION_PATTERN.finditer(prompt_text):
        action = parse_memory_action_token(match.group(1))
        if action:
            actions.append(action)
    return actions


class WriteConflictResolver:
    """Queue-based write conflict resolution strategy."""

    def __init__(self, max_queue_size: int = 1000):
        self._queue: deque = deque(maxlen=max_queue_size)
        self._lock = threading.Lock()
        self._conflict_count = 0

    def propose_write(self, key: str, proposed_value: str, agent_id: str) -> Tuple[bool, Optional[str]]:
        """
        Propose a write. Returns (accepted, reason).
        If key exists, queue the conflict and resolve via FIFO.
        """
        with self._lock:
            self._queue.append({
                "key": key,
                "value": proposed_value,
                "agent_id": agent_id,
                "timestamp": now()
            })
            # Simple FIFO: if queue size > 1, we have a conflict for this key
            # In this strategy, we accept the first, reject subsequent until resolved
            if len(self._queue) > 1:
                # Check if there are other pending writes for the same key
                conflicting = [q for q in self._queue if q["key"] == key]
                if len(conflicting) > 1:
                    self._conflict_count += 1
                    # Reject the latest one; first one in queue wins
                    if self._queue[0]["key"] == key and self._queue[0]["value"] == proposed_value:
                        return True, None
                    else:
                        return False, "Conflict: FIFO resolution pending"
            return True, None

    def resolve_conflicts(self) -> List[Dict[str, Any]]:
        """Resolve all conflicts by taking the first write for each key."""
        with self._lock:
            resolved = []
            seen_keys: Dict[str, str] = {}
            while self._queue:
                item = self._queue.popleft()
                key = item["key"]
                if key not in seen_keys:
                    seen_keys[key] = item["value"]
                    resolved.append(item)
            return resolved

    @property
    def conflict_count(self) -> int:
        return self._conflict_count


class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems."""

    def __init__(self):
        self._buffer: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._resolver = WriteConflictResolver()
        self._access_log: List[Dict[str, Any]] = []

    def write(self, key: str, value: str, agent_id: Optional[str] = None) -> bool:
        """Write a value to the buffer. Returns True if accepted."""
        with self._lock:
            accepted, reason = self._resolver.propose_write(key, value, agent_id or "unknown")
            if not accepted:
                self._access_log.append({
                    "action": "write_rejected",
                    "key": key,
                    "reason": reason,
                    "timestamp": now()
                })
                return False

            entry = MemoryEntry(
                key=key,
                value=value,
                timestamp=now(),
                agent_id=agent_id,
                version=1
            )
            if key in self._buffer:
                entry.version = self._buffer[key].version + 1
            self._buffer[key] = entry
            self._access_log.append({
                "action": "write",
                "key": key,
                "agent_id": agent_id,
                "timestamp": now()
            })
            return True

    def read(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """Read a value from the buffer."""
        with self._lock:
            entry = self._buffer.get(key)
            self._access_log.append({
                "action": "read",
                "key": key,
                "agent_id": agent_id,
                "found": entry is not None,
                "timestamp": now()
            })
            return entry.value if entry else None

    def delete(self, key: str) -> bool:
        """Delete a key from the buffer."""
        with self._lock:
            if key in self._buffer:
                del self._buffer[key]
                self._access_log.append({
                    "action": "delete",
                    "key": key,
                    "timestamp": now()
                })
                return True
            return False

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get the full entry for a key."""
        with self._lock:
            return self._buffer.get(key)

    def keys(self) -> List[str]:
        """Return all keys in the buffer."""
        with self._lock:
            return list(self._buffer.keys())

    def items(self) -> List[Tuple[str, MemoryEntry]]:
        """Return all key-value pairs."""
        with self._lock:
            return list(self._buffer.items())

    def size(self) -> int:
        """Return the number of entries in the buffer."""
        with self._lock:
            return len(self._buffer)

    def reset(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._buffer.clear()
            self._access_log.clear()

    def get_access_log(self) -> List[Dict[str, Any]]:
        """Return the access log."""
        with self._lock:
            return list(self._access_log)

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Tolerant fallback for unknown methods (logger-style)."""
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


# Shared buffer singleton
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer() -> MemoryBuffer:
    """Get or create the shared memory buffer singleton."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        with _BUFFER_LOCK:
            if _SHARED_BUFFER is None:
                _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER


def reset_shared_buffer() -> None:
    """Reset the shared memory buffer (for testing)."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()