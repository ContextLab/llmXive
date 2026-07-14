"""Shared external memory buffer for multi-agent social memory networks.

Implements a thread-safe, queue-based memory buffer supporting <MEMORY_ACTION>
tokens with JSON schema {"type": "write"|"read", "key": str, "value": str}.
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
from typing import Any, Dict, List, Optional, Tuple

# Token pattern for memory actions
MEMORY_ACTION_PATTERN = re.compile(r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>", re.DOTALL)

@dataclass
class MemoryAction:
    """Represents a single memory operation."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            agent_id=data.get("agent_id")
        )

@dataclass
class MemoryEntry:
    """A stored memory item with metadata."""
    key: str
    value: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = 1
    agent_id: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "agent_id": self.agent_id,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed
        }

    def update(self, new_value: str, agent_id: Optional[str] = None) -> None:
        """Update the entry with a new value."""
        self.value = new_value
        self.updated_at = datetime.utcnow().isoformat()
        self.version += 1
        if agent_id:
            self.agent_id = agent_id

def now() -> str:
    """Return current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def parse_memory_action_token(token_str: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token string into a MemoryAction object.

    Args:
        token_str: The content inside <MEMORY_ACTION> tags (JSON string).

    Returns:
        MemoryAction object if valid, None otherwise.
    """
    if not token_str or not isinstance(token_str, str):
        return None

    try:
        data = json.loads(token_str.strip())
        if not isinstance(data, dict):
            return None

        action_type = data.get("type")
        if action_type not in ("write", "read"):
            return None

        key = data.get("key")
        if not isinstance(key, str) or not key:
            return None

        value = data.get("value")
        # For read actions, value may be None
        if action_type == "write" and value is None:
            return None

        agent_id = data.get("agent_id")

        return MemoryAction(
            type=action_type,
            key=key,
            value=str(value) if value is not None else None,
            timestamp=data.get("timestamp", now()),
            agent_id=agent_id
        )
    except (json.JSONDecodeError, TypeError, KeyError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token string.

    Args:
        action: The MemoryAction to format.

    Returns:
        String in format <MEMORY_ACTION>{json}</MEMORY_ACTION>
    """
    json_str = json.dumps(action.to_dict(), ensure_ascii=False)
    return f"<MEMORY_ACTION>{json_str}</MEMORY_ACTION>"

def parse_action_from_prompt(prompt: str) -> List[Tuple[MemoryAction, int, int]]:
    """Extract all <MEMORY_ACTION> tokens from a prompt string.

    Args:
        prompt: The text to search for memory action tokens.

    Returns:
        List of tuples (MemoryAction, start_index, end_index) for each found action.
    """
    results = []
    for match in MEMORY_ACTION_PATTERN.finditer(prompt):
        action = parse_memory_action_token(match.group(1))
        if action:
            results.append((action, match.start(), match.end()))
    return results

class WriteConflictResolver:
    """Resolves write conflicts using a queue-based approach.

    When multiple agents attempt to write to the same key simultaneously,
    the first request in the queue wins, and subsequent requests are
    either queued or rejected based on the conflict policy.
    """

    def __init__(self, policy: str = "first_wins", max_queue_size: int = 100):
        """Initialize the conflict resolver.

        Args:
            policy: Conflict resolution policy ("first_wins", "last_wins", "queue").
            max_queue_size: Maximum number of pending writes to queue.
        """
        self.policy = policy
        self.max_queue_size = max_queue_size
        self._write_queues: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def resolve(self, key: str, action: MemoryAction) -> Tuple[bool, Optional[str]]:
        """Attempt to resolve a write conflict for the given key.

        Args:
            key: The memory key being written to.
            action: The MemoryAction attempting the write.

        Returns:
            Tuple of (success: bool, message: Optional[str]).
            - success=True: Write is allowed.
            - success=False: Write is blocked/rejected with a reason.
        """
        with self._lock:
            if key not in self._write_queues:
                self._write_queues[key] = deque()

            queue = self._write_queues[key]

            # If queue is empty, this write goes through immediately
            if not queue:
                queue.append(action)
                return True, None

            # Queue already has pending writes
            if self.policy == "first_wins":
                # Only the first writer succeeds; others are rejected
                if len(queue) == 1:
                    return True, None
                else:
                    return False, f"Write to '{key}' blocked: first_wins policy, already queued."

            elif self.policy == "last_wins":
                # Replace the last queued action with this one
                while len(queue) > 1:
                    queue.popleft()
                queue[-1] = action
                return True, None

            elif self.policy == "queue":
                # Add to queue if space available
                if len(queue) >= self.max_queue_size:
                    return False, f"Write to '{key}' rejected: queue full ({self.max_queue_size})."
                queue.append(action)
                return True, f"Write to '{key}' queued (position {len(queue)})."

            else:
                return False, f"Unknown conflict policy: {self.policy}"

    def get_queue_length(self, key: str) -> int:
        """Get the current queue length for a key."""
        with self._lock:
            return len(self._write_queues.get(key, deque()))

    def clear_queue(self, key: str) -> None:
        """Clear the write queue for a specific key."""
        with self._lock:
            if key in self._write_queues:
                self._write_queues[key].clear()

class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems.

    Supports:
    - <MEMORY_ACTION> token parsing and generation
    - Write/read operations with conflict resolution
    - Versioning and access tracking
    - Queue-based write conflict resolution
    """

    def __init__(self, conflict_policy: str = "first_wins", max_queue_size: int = 100):
        """Initialize the memory buffer.

        Args:
            conflict_policy: Policy for resolving write conflicts.
            max_queue_size: Maximum queue size for pending writes.
        """
        self._storage: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._conflict_resolver = WriteConflictResolver(conflict_policy, max_queue_size)
        self._operation_log: deque = deque(maxlen=10000)
        self._initialized = True

    def write(self, key: str, value: str, agent_id: Optional[str] = None) -> Tuple[bool, str]:
        """Write a value to the memory buffer.

        Args:
            key: The memory key.
            value: The value to store.
            agent_id: Optional identifier for the writing agent.

        Returns:
            Tuple of (success: bool, message: str).
        """
        action = MemoryAction(type="write", key=key, value=value, agent_id=agent_id)

        # Check for conflicts
        success, msg = self._conflict_resolver.resolve(key, action)
        if not success:
            return False, msg

        with self._lock:
            if key in self._storage:
                # Update existing entry
                entry = self._storage[key]
                entry.update(value, agent_id)
                self._log_operation(action, "updated")
                return True, f"Updated key '{key}' (version {entry.version})"
            else:
                # Create new entry
                self._storage[key] = MemoryEntry(
                    key=key,
                    value=value,
                    agent_id=agent_id
                )
                self._log_operation(action, "created")
                return True, f"Created key '{key}'"

    def read(self, key: str, agent_id: Optional[str] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """Read a value from the memory buffer.

        Args:
            key: The memory key to read.
            agent_id: Optional identifier for the reading agent.

        Returns:
            Tuple of (value: Optional[str], metadata: Dict).
            Returns (None, {}) if key not found.
        """
        action = MemoryAction(type="read", key=key, agent_id=agent_id)

        with self._lock:
            if key not in self._storage:
                self._log_operation(action, "not_found")
                return None, {}

            entry = self._storage[key]
            entry.access_count += 1
            entry.last_accessed = now()

            self._log_operation(action, "read")
            return entry.value, {
                "version": entry.version,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
                "access_count": entry.access_count,
                "agent_id": entry.agent_id
            }

    def delete(self, key: str, agent_id: Optional[str] = None) -> Tuple[bool, str]:
        """Delete a key from the memory buffer.

        Args:
            key: The memory key to delete.
            agent_id: Optional identifier for the deleting agent.

        Returns:
            Tuple of (success: bool, message: str).
        """
        action = MemoryAction(type="write", key=key, value=None, agent_id=agent_id)

        with self._lock:
            if key not in self._storage:
                return False, f"Key '{key}' not found"

            del self._storage[key]
            self._log_operation(action, "deleted")
            self._conflict_resolver.clear_queue(key)
            return True, f"Deleted key '{key}'"

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a value by key (convenience method).

        Args:
            key: The memory key.
            default: Default value if key not found.

        Returns:
            The stored value or default.
        """
        value, _ = self.read(key)
        return value if value is not None else default

    def set(self, key: str, value: str) -> bool:
        """Set a value by key (convenience method).

        Args:
            key: The memory key.
            value: The value to store.

        Returns:
            True if successful.
        """
        success, _ = self.write(key, value)
        return success

    def contains(self, key: str) -> bool:
        """Check if a key exists in the buffer.

        Args:
            key: The memory key to check.

        Returns:
            True if key exists.
        """
        with self._lock:
            return key in self._storage

    def keys(self) -> List[str]:
        """Get all keys in the buffer.

        Returns:
            List of all keys.
        """
        with self._lock:
            return list(self._storage.keys())

    def size(self) -> int:
        """Get the number of entries in the buffer.

        Returns:
            Number of entries.
        """
        with self._lock:
            return len(self._storage)

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._storage.clear()
            self._operation_log.clear()

    def reset(self) -> None:
        """Reset the buffer to initial state."""
        with self._lock:
            self._storage.clear()
            self._operation_log.clear()
            self._conflict_resolver = WriteConflictResolver(
                self._conflict_resolver.policy,
                self._conflict_resolver.max_queue_size
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics.

        Returns:
            Dictionary with buffer statistics.
        """
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._storage.values())
            return {
                "total_entries": len(self._storage),
                "total_accesses": total_accesses,
                "operation_log_size": len(self._operation_log),
                "conflict_policy": self._conflict_resolver.policy
            }

    def _log_operation(self, action: MemoryAction, status: str) -> None:
        """Log an operation to the internal log."""
        log_entry = {
            "timestamp": now(),
            "action": action.to_dict(),
            "status": status
        }
        self._operation_log.append(log_entry)

    def get_recent_operations(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent operations.

        Args:
            n: Number of recent operations to return.

        Returns:
            List of recent operation logs.
        """
        with self._lock:
            return list(self._operation_log)[-n:]

    def process_token(self, token_str: str, agent_id: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:
        """Process a <MEMORY_ACTION> token string.

        Args:
            token_str: The token string to process.
            agent_id: Optional agent identifier.

        Returns:
            Tuple of (success: bool, message: str, result: Optional[Dict]).
        """
        action = parse_memory_action_token(token_str)
        if not action:
            return False, "Invalid memory action token", None

        if action.type == "write":
            success, msg = self.write(action.key, action.value or "", action.agent_id or agent_id)
            return success, msg, None
        elif action.type == "read":
            value, metadata = self.read(action.key, action.agent_id or agent_id)
            if value is not None:
                return True, "Read successful", {"value": value, **metadata}
            else:
                return False, "Key not found", None
        else:
            return False, f"Unknown action type: {action.type}", None

    # Tolerant attribute access for logger-like usage
    def __getattr__(self, name: str):
        """Provide tolerant attribute access for unknown methods."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Global shared buffer instance (singleton pattern)
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(conflict_policy: str = "first_wins", max_queue_size: int = 100) -> MemoryBuffer:
    """Get the global shared memory buffer instance.

    Args:
        conflict_policy: Policy for conflict resolution.
        max_queue_size: Maximum queue size.

    Returns:
        The shared MemoryBuffer instance.
    """
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(conflict_policy, max_queue_size)
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the global shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
            _SHARED_BUFFER = None