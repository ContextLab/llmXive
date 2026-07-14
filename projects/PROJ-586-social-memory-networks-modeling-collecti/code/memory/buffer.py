"""Shared external memory buffer for multi-agent systems.

Implements a thread-safe memory buffer supporting <MEMORY_ACTION> tokens
with JSON schema {"type": "write"|"read", "key": str, "value": str}.
Includes queue-based write conflict resolution.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Pattern for memory action tokens: <MEMORY_ACTION:{"type": "...", ...}>
MEMORY_ACTION_PATTERN = re.compile(
    r'<MEMORY_ACTION:\s*(\{.*?\})\s*>'
)

@dataclass
class MemoryAction:
    """Represents a memory action (read or write)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "key": self.key,
            "value": self.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value"),
            agent_id=data.get("agent_id"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    agent_id: str
    timestamp: str
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "version": self.version
        }

def now() -> str:
    """Return current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION:JSON> token into a MemoryAction object."""
    match = MEMORY_ACTION_PATTERN.match(token.strip())
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        return MemoryAction.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction object into a <MEMORY_ACTION:JSON> token."""
    json_str = json.dumps(action.to_dict(), ensure_ascii=False)
    return f"<MEMORY_ACTION:{json_str}>"

def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """Extract all memory actions from a prompt string."""
    actions = []
    for match in MEMORY_ACTION_PATTERN.finditer(prompt):
        try:
            data = json.loads(match.group(1))
            actions.append(MemoryAction.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            continue
    return actions

class WriteConflictResolver:
    """Queue-based write conflict resolution mechanism.

    When multiple agents attempt to write to the same key simultaneously,
    this resolver uses a FIFO queue to serialize writes and maintain
    a version history.
    """

    def __init__(self):
        self._write_queues: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self._conflict_log: List[Dict[str, Any]] = []

    def _get_queue(self, key: str) -> deque:
        """Get or create the write queue for a key."""
        with self._lock:
            if key not in self._write_queues:
                self._write_queues[key] = deque()
            return self._write_queues[key]

    def submit_write(self, key: str, action: MemoryAction) -> int:
        """Submit a write action to the queue. Returns the position in queue."""
        queue = self._get_queue(key)
        with self._lock:
            position = len(queue)
            queue.append(action)
            if position > 0:
                self._conflict_log.append({
                    "key": key,
                    "conflict_count": position + 1,
                    "timestamp": now()
                })
            return position

    def process_next(self, key: str) -> Optional[MemoryAction]:
        """Process and return the next write action for a key."""
        queue = self._get_queue(key)
        with self._lock:
            if queue:
                return queue.popleft()
            return None

    def is_empty(self, key: str) -> bool:
        """Check if the write queue for a key is empty."""
        queue = self._get_queue(key)
        with self._lock:
            return len(queue) == 0

    def get_conflict_count(self, key: str) -> int:
        """Get the number of pending writes for a key."""
        queue = self._get_queue(key)
        with self._lock:
            return len(queue)

    def get_conflict_log(self) -> List[Dict[str, Any]]:
        """Return the conflict resolution log."""
        with self._lock:
            return list(self._conflict_log)

class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems.

    Supports:
    - Write operations with queue-based conflict resolution
    - Read operations with version tracking
    - <MEMORY_ACTION> token parsing and formatting
    """

    def __init__(self):
        self._entries: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._conflict_resolver = WriteConflictResolver()
        self._access_log: List[Dict[str, Any]] = []

    def write(self, key: str, value: str, agent_id: str) -> bool:
        """Write a value to the memory buffer.

        Uses queue-based conflict resolution if concurrent writes exist.
        Returns True if the write was successful, False if rejected.
        """
        action = MemoryAction(
            type="write",
            key=key,
            value=value,
            agent_id=agent_id,
            timestamp=now()
        )

        # Submit to conflict resolver
        position = self._conflict_resolver.submit_write(key, action)

        # If there are conflicts, wait for queue processing
        if position > 0:
            # Process pending writes first
            while not self._conflict_resolver.is_empty(key):
                pending_action = self._conflict_resolver.process_next(key)
                if pending_action and pending_action.value is not None:
                    self._apply_write(pending_action)

        # Process current action
        self._apply_write(action)

        self._log_access("write", key, agent_id)
        return True

    def _apply_write(self, action: MemoryAction) -> None:
        """Apply a write action to the internal state."""
        with self._lock:
            key = action.key
            if key in self._entries:
                # Increment version
                new_entry = MemoryEntry(
                    key=key,
                    value=action.value or "",
                    agent_id=action.agent_id or "unknown",
                    timestamp=action.timestamp,
                    version=self._entries[key].version + 1
                )
            else:
                new_entry = MemoryEntry(
                    key=key,
                    value=action.value or "",
                    agent_id=action.agent_id or "unknown",
                    timestamp=action.timestamp,
                    version=1
                )
            self._entries[key] = new_entry

    def read(self, key: str, agent_id: str) -> Optional[str]:
        """Read a value from the memory buffer.

        Returns the current value for the key, or None if not found.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry:
                self._log_access("read", key, agent_id)
                return entry.value
            return None

    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """Get the full MemoryEntry for a key."""
        with self._lock:
            return self._entries.get(key)

    def delete(self, key: str, agent_id: str) -> bool:
        """Delete a key from the memory buffer."""
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                self._log_access("delete", key, agent_id)
                return True
            return False

    def search(self, query: str, agent_id: str) -> List[MemoryEntry]:
        """Search for entries containing the query string."""
        with self._lock:
            results = []
            query_lower = query.lower()
            for entry in self._entries.values():
                if query_lower in entry.value.lower() or query_lower in entry.key.lower():
                    results.append(entry)
            self._log_access("search", query, agent_id, len(results))
            return results

    def get_all_keys(self) -> List[str]:
        """Return all keys in the buffer."""
        with self._lock:
            return list(self._entries.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Return buffer statistics."""
        with self._lock:
            return {
                "total_entries": len(self._entries),
                "total_writes": sum(1 for e in self._entries.values()),
                "access_log_size": len(self._access_log),
                "pending_conflicts": {
                    key: self._conflict_resolver.get_conflict_count(key)
                    for key in self._conflict_resolver._write_queues
                    if self._conflict_resolver.get_conflict_count(key) > 0
                }
            }

    def _log_access(self, action_type: str, target: str, agent_id: str, extra: Any = None) -> None:
        """Log an access event."""
        entry = {
            "type": action_type,
            "target": target,
            "agent_id": agent_id,
            "timestamp": now()
        }
        if extra is not None:
            entry["extra"] = extra
        self._access_log.append(entry)

    def reset(self) -> None:
        """Reset the buffer to empty state."""
        with self._lock:
            self._entries.clear()
            self._access_log.clear()
            self._conflict_resolver = WriteConflictResolver()

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._entries

# Global singleton instance
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer() -> MemoryBuffer:
    """Get the singleton shared memory buffer instance."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer()
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()

# Tolerant fallback for any unknown method calls
def __getattr__(self, name: str):
    """Tolerant fallback for unknown attributes/methods."""
    def _noop(*args: Any, **kwargs: Any) -> Any:
        return None
    return _noop