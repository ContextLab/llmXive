"""Shared external memory buffer with queue-based conflict resolution.

Implements a thread-safe memory buffer that supports <MEMORY_ACTION> tokens
with JSON schema {"type": "write"|"read", "key": str, "value": str}.
Write conflicts are resolved using a FIFO queue-based approach.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.logging import get_logger

logger = get_logger(__name__)

# Token marker for memory actions
MEMORY_ACTION_TOKEN = "<MEMORY_ACTION>"

@dataclass
class MemoryAction:
    """Represents a memory action (write or read)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None  # Only for write actions
    timestamp: float = field(default_factory=time.time)
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        """Create from dictionary representation."""
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value"),
            timestamp=data.get("timestamp", time.time()),
            agent_id=data.get("agent_id")
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryAction":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

@dataclass
class MemoryEntry:
    """Represents a stored memory entry."""
    key: str
    value: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: Optional[float] = None
    version: int = 1
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "version": self.version,
            "agent_id": self.agent_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary representation."""
        return cls(
            key=data["key"],
            value=data["value"],
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
            version=data.get("version", 1),
            agent_id=data.get("agent_id")
        )

def now() -> float:
    """Return current timestamp."""
    return time.time()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token string into a MemoryAction object.

    Expected format: <MEMORY_ACTION>{"type": "write", "key": "...", "value": "..."}
    """
    if not token.startswith(MEMORY_ACTION_TOKEN):
        return None

    json_part = token[len(MEMORY_ACTION_TOKEN):]

    try:
        data = json.loads(json_part)
        return MemoryAction.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse memory action token: {e}")
        return None

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token string."""
    json_str = action.to_json()
    return f"{MEMORY_ACTION_TOKEN}{json_str}"

def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """Extract all memory actions from a prompt string.

    Searches for all occurrences of <MEMORY_ACTION>... tokens.
    """
    pattern = re.escape(MEMORY_ACTION_TOKEN) + r'\{.*?\}'
    matches = re.findall(pattern, prompt, re.DOTALL)
    actions = []

    for match in matches:
        action = parse_memory_action_token(match)
        if action:
            actions.append(action)

    return actions

class WriteConflictResolver:
    """Resolves write conflicts using queue-based approach.

    When multiple agents try to write to the same key, actions are queued
    and processed in FIFO order. The last write wins, but all intermediate
    states are logged for audit purposes.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.write_queue: deque = deque()
        self.conflict_log: List[Dict[str, Any]] = []

    def queue_write(self, action: MemoryAction) -> int:
        """Queue a write action and return its position in the queue."""
        with self.lock:
            position = len(self.write_queue)
            self.write_queue.append(action)
            return position

    def process_queue(self, buffer: "MemoryBuffer") -> List[Tuple[str, str]]:
        """Process all queued writes in order, resolving conflicts.

        Returns a list of (key, value) pairs that were successfully written.
        """
        written = []

        with self.lock:
            while self.write_queue:
                action = self.write_queue.popleft()

                if action.type == "write" and action.key and action.value:
                    # Check if this key already exists (conflict)
                    existing = buffer.get(action.key)
                    if existing:
                        # Log the conflict
                        self.conflict_log.append({
                            "key": action.key,
                            "conflicting_agent": existing.agent_id,
                            "new_agent": action.agent_id,
                            "old_value": existing.value,
                            "new_value": action.value,
                            "timestamp": action.timestamp
                        })
                        logger.debug(f"Write conflict resolved for key '{action.key}': "
                                   f"overwriting value from agent {existing.agent_id}")

                    # Perform the write
                    buffer._write_to_store(action)
                    written.append((action.key, action.value))

        return written

    def get_conflict_count(self) -> int:
        """Return the number of conflicts encountered."""
        return len(self.conflict_log)

    def get_conflict_log(self) -> List[Dict[str, Any]]:
        """Return the full conflict log."""
        return list(self.conflict_log)

class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems.

    Supports:
    - Write operations with conflict resolution
    - Read operations with access tracking
    - Queue-based conflict resolution for concurrent writes
    - Memory action token parsing/formatting
    """

    def __init__(self, capacity: Optional[int] = None):
        self.store: Dict[str, MemoryEntry] = {}
        self.lock = threading.RLock()
        self.capacity = capacity
        self.conflict_resolver = WriteConflictResolver()
        self.stats = {
            "total_writes": 0,
            "total_reads": 0,
            "conflicts": 0,
            "evictions": 0
        }

    def write(self, key: str, value: str, agent_id: Optional[str] = None) -> bool:
        """Write a value to the memory buffer.

        If the key already exists, the new value overwrites the old one
        and the conflict is logged.
        """
        with self.lock:
            action = MemoryAction(
                type="write",
                key=key,
                value=value,
                agent_id=agent_id
            )

            # Queue the write for conflict resolution
            self.conflict_resolver.queue_write(action)

            # Process the queue immediately (for synchronous behavior)
            self.conflict_resolver.process_queue(self)

            self.stats["total_writes"] += 1
            return True

    def read(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """Read a value from the memory buffer.

        Returns None if the key doesn't exist.
        Updates access tracking on successful reads.
        """
        with self.lock:
            self.stats["total_reads"] += 1

            if key not in self.store:
                return None

            entry = self.store[key]
            entry.access_count += 1
            entry.last_accessed = time.time()

            return entry.value

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get the full memory entry (not just the value)."""
        with self.lock:
            return self.store.get(key)

    def delete(self, key: str) -> bool:
        """Delete a key from the memory buffer."""
        with self.lock:
            if key in self.store:
                del self.store[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the buffer."""
        with self.lock:
            return key in self.store

    def get_all_keys(self) -> List[str]:
        """Return all keys in the buffer."""
        with self.lock:
            return list(self.store.keys())

    def get_all_entries(self) -> Dict[str, MemoryEntry]:
        """Return all entries in the buffer."""
        with self.lock:
            return dict(self.store)

    def search(self, pattern: str) -> List[Tuple[str, str]]:
        """Search for keys matching a pattern (simple substring match).

        Returns list of (key, value) pairs.
        """
        with self.lock:
            results = []
            for key, entry in self.store.items():
                if pattern.lower() in key.lower() or pattern.lower() in entry.value.lower():
                    results.append((key, entry.value))
            return results

    def _write_to_store(self, action: MemoryAction) -> None:
        """Internal method to write directly to the store (for conflict resolution)."""
        if action.type != "write" or not action.key or action.value is None:
            return

        current_time = time.time()

        if action.key in self.store:
            # Update existing entry
            entry = self.store[action.key]
            entry.value = action.value
            entry.updated_at = current_time
            entry.version += 1
            entry.agent_id = action.agent_id
        else:
            # Create new entry
            # Check capacity
            if self.capacity and len(self.store) >= self.capacity:
                # Evict least recently accessed entry
                self._evict_lru()

            self.store[action.key] = MemoryEntry(
                key=action.key,
                value=action.value,
                created_at=current_time,
                updated_at=current_time,
                access_count=0,
                last_accessed=None,
                version=1,
                agent_id=action.agent_id
            )

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self.store:
            return

        # Find entry with oldest last_accessed or created_at
        oldest_key = None
        oldest_time = float('inf')

        for key, entry in self.store.items():
            access_time = entry.last_accessed or entry.created_at
            if access_time < oldest_time:
                oldest_time = access_time
                oldest_key = key

        if oldest_key:
            del self.store[oldest_key]
            self.stats["evictions"] += 1

    def reset(self) -> None:
        """Reset the buffer to empty state."""
        with self.lock:
            self.store.clear()
            self.stats = {
                "total_writes": 0,
                "total_reads": 0,
                "conflicts": 0,
                "evictions": 0
            }
            self.conflict_resolver = WriteConflictResolver()

    def get_stats(self) -> Dict[str, Any]:
        """Return buffer statistics."""
        with self.lock:
            stats = dict(self.stats)
            stats["current_size"] = len(self.store)
            stats["capacity"] = self.capacity
            stats["conflicts_resolved"] = self.conflict_resolver.get_conflict_count()
            return stats

    def __len__(self) -> int:
        """Return the number of entries in the buffer."""
        with self.lock:
            return len(self.store)

    def __contains__(self, key: str) -> bool:
        """Check if key is in the buffer."""
        return self.exists(key)

    def __getitem__(self, key: str) -> Optional[str]:
        """Get value by key (dict-like access)."""
        return self.read(key)

    def __setitem__(self, key: str, value: str) -> None:
        """Set value by key (dict-like access)."""
        self.write(key, value)

# Shared buffer singleton
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(capacity: Optional[int] = None) -> MemoryBuffer:
    """Get or create the shared memory buffer singleton."""
    global _SHARED_BUFFER

    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(capacity=capacity)

    return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the shared memory buffer to empty state."""
    global _SHARED_BUFFER

    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()

# Utility functions for token parsing in prompts
def extract_memory_actions_from_text(text: str) -> List[MemoryAction]:
    """Extract all memory actions from a text string.

    This is a convenience wrapper around parse_action_from_prompt.
    """
    return parse_action_from_prompt(text)

def format_memory_action(action: MemoryAction) -> str:
    """Format a memory action as a token string.

    This is a convenience wrapper around format_action_token.
    """
    return format_action_token(action)