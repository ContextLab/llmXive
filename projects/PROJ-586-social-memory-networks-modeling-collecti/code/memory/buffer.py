"""Shared external memory buffer with queue-based conflict resolution.

Implements a thread-safe memory buffer that supports <MEMORY_ACTION> tokens
with JSON schema {"type": "write"|"read", "key": str, "value": str}.
Writes are queued and resolved in FIFO order to prevent conflicts.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Token pattern for memory actions
MEMORY_ACTION_PATTERN = re.compile(r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>")

@dataclass
class MemoryAction:
    """Represents a memory action (write or read)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "key": self.key,
            "value": self.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        """Create from dictionary."""
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value")
        )

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    timestamp: float
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id
        }

def now() -> float:
    """Return current timestamp."""
    return time.time()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token string into a MemoryAction object."""
    match = MEMORY_ACTION_PATTERN.search(token)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        return MemoryAction.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token string."""
    return f"<MEMORY_ACTION>{json.dumps(action.to_dict())}</MEMORY_ACTION>"

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
    """Handles write conflicts using FIFO queue-based resolution."""

    def __init__(self):
        self._write_queue: deque = deque()
        self._lock = threading.Lock()
        self._processing = False

    def enqueue_write(self, action: MemoryAction, agent_id: Optional[str] = None) -> int:
        """Add a write action to the queue. Returns queue position."""
        with self._lock:
            position = len(self._write_queue)
            self._write_queue.append({
                "action": action,
                "agent_id": agent_id,
                "timestamp": now()
            })
            return position

    def process_next(self) -> Optional[Tuple[MemoryAction, Optional[str]]]:
        """Process the next write in the queue. Returns (action, agent_id) or None."""
        with self._lock:
            if not self._write_queue:
                return None
            entry = self._write_queue.popleft()
            return entry["action"], entry["agent_id"]

    def is_empty(self) -> bool:
        """Check if the write queue is empty."""
        with self._lock:
            return len(self._write_queue) == 0

    def queue_length(self) -> int:
        """Return the number of pending writes."""
        with self._lock:
            return len(self._write_queue)

    def reset(self) -> None:
        """Clear the write queue."""
        with self._lock:
            self._write_queue.clear()

class MemoryBuffer:
    """Thread-safe shared memory buffer with conflict resolution.

    Supports:
    - Write operations: queue-based FIFO resolution for conflicts
    - Read operations: direct lookup with optional fallback to queue
    - <MEMORY_ACTION> token parsing and generation
    """

    def __init__(self):
        self._storage: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._conflict_resolver = WriteConflictResolver()
        self._history: List[Dict[str, Any]] = []

    def write(self, key: str, value: str, agent_id: Optional[str] = None) -> bool:
        """Write a value to the buffer. Uses queue-based conflict resolution.

        Returns True if write was successful (after conflict resolution).
        """
        action = MemoryAction(type="write", key=key, value=value)
        position = self._conflict_resolver.enqueue_write(action, agent_id)

        # Process the write from the queue
        while True:
            next_action, next_agent = self._conflict_resolver.process_next()
            if next_action is None:
                break
            if next_action == action:
                # This is our turn to write
                with self._lock:
                    self._storage[key] = MemoryEntry(
                        key=key,
                        value=value,
                        timestamp=now(),
                        agent_id=agent_id
                    )
                    self._history.append({
                        "action": "write",
                        "key": key,
                        "value": value,
                        "agent_id": agent_id,
                        "timestamp": now(),
                        "queue_position": position
                    })
                return True
            # Process other writes first (FIFO order)

        return False

    def read(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """Read a value from the buffer.

        Returns the value if found, None otherwise.
        """
        with self._lock:
            if key in self._storage:
                entry = self._storage[key]
                self._history.append({
                    "action": "read",
                    "key": key,
                    "value": entry.value,
                    "agent_id": agent_id,
                    "timestamp": now()
                })
                return entry.value
            return None

    def delete(self, key: str, agent_id: Optional[str] = None) -> bool:
        """Delete a key from the buffer."""
        with self._lock:
            if key in self._storage:
                del self._storage[key]
                self._history.append({
                    "action": "delete",
                    "key": key,
                    "agent_id": agent_id,
                    "timestamp": now()
                })
                return True
            return False

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a value with optional default."""
        return self.read(key) or default

    def keys(self) -> List[str]:
        """Return all keys in the buffer."""
        with self._lock:
            return list(self._storage.keys())

    def __contains__(self, key: str) -> bool:
        """Check if key exists in buffer."""
        with self._lock:
            return key in self._storage

    def __len__(self) -> int:
        """Return number of entries in buffer."""
        with self._lock:
            return len(self._storage)

    def reset(self) -> None:
        """Reset the buffer to empty state."""
        with self._lock:
            self._storage.clear()
            self._history.clear()
        self._conflict_resolver.reset()

    def get_history(self) -> List[Dict[str, Any]]:
        """Return the operation history."""
        with self._lock:
            return list(self._history)

    def parse_and_execute(self, token: str, agent_id: Optional[str] = None) -> Optional[Any]:
        """Parse a <MEMORY_ACTION> token and execute it.

        Returns the result of the operation (value for reads, True/False for writes).
        """
        action = parse_memory_action_token(token)
        if action is None:
            return None

        if action.type == "write":
            return self.write(action.key, action.value, agent_id)
        elif action.type == "read":
            return self.read(action.key, agent_id)
        return None

    def execute_actions_from_prompt(self, prompt: str, agent_id: Optional[str] = None) -> List[Any]:
        """Extract and execute all memory actions from a prompt.

        Returns list of results in order.
        """
        actions = parse_action_from_prompt(prompt)
        results = []
        for action in actions:
            if action.type == "write":
                results.append(self.write(action.key, action.value, agent_id))
            elif action.type == "read":
                results.append(self.read(action.key, agent_id))
        return results

# Shared buffer singleton
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer() -> MemoryBuffer:
    """Get the global shared memory buffer (singleton)."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer()
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the global shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
        _SHARED_BUFFER = None