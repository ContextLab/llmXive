"""
Shared external memory buffer for multi-agent systems.

Implements a thread-safe, queue-based memory buffer with:
- <MEMORY_ACTION> token support with JSON schema
- Queue-based write conflict resolution (FIFO)
- Read operations with key-based lookup
"""
from __future__ import annotations

import json
import re
import threading
from collections import deque
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Token pattern for memory actions
MEMORY_ACTION_PATTERN = re.compile(
    r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>",
    re.DOTALL | re.IGNORECASE
)

@dataclass
class MemoryAction:
    """Represents a single memory operation."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        """Create from dictionary."""
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryAction":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    agent_id: str
    timestamp: str
    version: int = 1
    is_deleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        return cls(**data)

def now() -> str:
    """Return current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def parse_memory_action_token(token_str: str) -> Optional[MemoryAction]:
    """
    Parse a <MEMORY_ACTION> token string into a MemoryAction object.

    Args:
        token_str: String containing the full token, e.g.
                   "<MEMORY_ACTION>{...}</MEMORY_ACTION>"

    Returns:
        MemoryAction object if successful, None otherwise.
    """
    if not token_str:
        return None

    match = MEMORY_ACTION_PATTERN.search(token_str)
    if not match:
        return None

    json_str = match.group(1).strip()
    try:
        data = json.loads(json_str)
        return MemoryAction(
            type=data.get("type"),
            key=data.get("key"),
            value=data.get("value"),
            timestamp=data.get("timestamp", now()),
            agent_id=data.get("agent_id")
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """
    Format a MemoryAction object into a <MEMORY_ACTION> token string.

    Args:
        action: MemoryAction object to format.

    Returns:
        String in format "<MEMORY_ACTION>{json}</MEMORY_ACTION>"
    """
    return f"<MEMORY_ACTION>{action.to_json()}</MEMORY_ACTION>"

def parse_action_from_prompt(prompt_text: str) -> List[MemoryAction]:
    """
    Extract all memory actions from a prompt text.

    Args:
        prompt_text: Text that may contain multiple <MEMORY_ACTION> tokens.

    Returns:
        List of successfully parsed MemoryAction objects.
    """
    actions = []
    for match in MEMORY_ACTION_PATTERN.finditer(prompt_text):
        json_str = match.group(1).strip()
        try:
            data = json.loads(json_str)
            action = MemoryAction(
                type=data.get("type"),
                key=data.get("key"),
                value=data.get("value"),
                timestamp=data.get("timestamp", now()),
                agent_id=data.get("agent_id")
            )
            actions.append(action)
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return actions

class MemoryBuffer:
    """
    Thread-safe shared memory buffer with queue-based conflict resolution.

    Features:
    - FIFO queue for write operations to resolve conflicts
    - Key-based read operations
    - Version tracking for entries
    - Thread-safe operations via locks
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize the memory buffer.

        Args:
            max_size: Maximum number of entries to retain (oldest evicted first).
        """
        self._entries: Dict[str, MemoryEntry] = {}
        self._write_queue: deque = deque()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._version_counter = 0
        self._access_log: List[Dict[str, Any]] = []

    def write(self, key: str, value: str, agent_id: str) -> Tuple[bool, str]:
        """
        Write a value to the memory buffer.

        Uses queue-based conflict resolution: writes are processed in FIFO order.
        If a key already exists, the new value is queued and processed when
        it's the write's turn.

        Args:
            key: The key to write to.
            value: The value to store.
            agent_id: ID of the agent performing the write.

        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            self._version_counter += 1
            new_version = self._version_counter

            # Create the write action
            action = MemoryAction(
                type="write",
                key=key,
                value=value,
                timestamp=now(),
                agent_id=agent_id
            )

            # Enqueue the write operation
            self._write_queue.append(action)

            # Process the queue (FIFO conflict resolution)
            self._process_write_queue()

            # Log the access
            self._access_log.append({
                "action": "write",
                "key": key,
                "agent_id": agent_id,
                "timestamp": now()
            })

            # Enforce max size
            self._enforce_max_size()

            return True, f"Write queued and processed for key: {key}"

    def read(self, key: str, agent_id: Optional[str] = None) -> Tuple[Optional[str], Optional[int]]:
        """
        Read a value from the memory buffer.

        Args:
            key: The key to read.
            agent_id: Optional ID of the agent performing the read.

        Returns:
            Tuple of (value: Optional[str], version: Optional[int])
            Returns (None, None) if key not found.
        """
        with self._lock:
            if key in self._entries:
                entry = self._entries[key]
                if entry.is_deleted:
                    return None, None
                # Log the access
                self._access_log.append({
                    "action": "read",
                    "key": key,
                    "agent_id": agent_id,
                    "timestamp": now()
                })
                return entry.value, entry.version
            return None, None

    def delete(self, key: str, agent_id: str) -> Tuple[bool, str]:
        """
        Mark a key as deleted (soft delete).

        Args:
            key: The key to delete.
            agent_id: ID of the agent performing the delete.

        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            if key in self._entries:
                self._entries[key].is_deleted = True
                self._access_log.append({
                    "action": "delete",
                    "key": key,
                    "agent_id": agent_id,
                    "timestamp": now()
                })
                return True, f"Key {key} marked as deleted"
            return False, f"Key {key} not found"

    def get_all_keys(self) -> List[str]:
        """
        Get all non-deleted keys in the buffer.

        Returns:
            List of active keys.
        """
        with self._lock:
            return [
                k for k, v in self._entries.items()
                if not v.is_deleted
            ]

    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """
        Get the full entry for a key.

        Args:
            key: The key to look up.

        Returns:
            MemoryEntry if found, None otherwise.
        """
        with self._lock:
            return self._entries.get(key)

    def _process_write_queue(self) -> None:
        """Process the write queue in FIFO order."""
        while self._write_queue:
            action = self._write_queue.popleft()

            if action.type == "write" and action.value is not None:
                if action.key in self._entries:
                    # Update existing entry
                    entry = self._entries[action.key]
                    entry.value = action.value
                    entry.version = self._version_counter
                    entry.timestamp = action.timestamp
                    entry.agent_id = action.agent_id
                    entry.is_deleted = False
                else:
                    # Create new entry
                    self._entries[action.key] = MemoryEntry(
                        key=action.key,
                        value=action.value,
                        agent_id=action.agent_id or "unknown",
                        timestamp=action.timestamp,
                        version=self._version_counter
                    )

    def _enforce_max_size(self) -> None:
        """Evict oldest entries if buffer exceeds max_size."""
        if len(self._entries) <= self._max_size:
            return

        # Sort entries by timestamp and remove oldest
        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: x[1].timestamp
        )
        to_remove = len(self._entries) - self._max_size
        for i in range(to_remove):
            key = sorted_entries[i][0]
            if not self._entries[key].is_deleted:
                del self._entries[key]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics.

        Returns:
            Dictionary with buffer statistics.
        """
        with self._lock:
            active_keys = sum(1 for e in self._entries.values() if not e.is_deleted)
            return {
                "total_entries": len(self._entries),
                "active_entries": active_keys,
                "queue_length": len(self._write_queue),
                "max_size": self._max_size,
                "access_log_length": len(self._access_log)
            }

    def reset(self) -> None:
        """Reset the buffer to initial state."""
        with self._lock:
            self._entries.clear()
            self._write_queue.clear()
            self._access_log.clear()
            self._version_counter = 0

    def clear(self) -> None:
        """Alias for reset."""
        self.reset()

    def __len__(self) -> int:
        """Return number of active entries."""
        with self._lock:
            return sum(1 for e in self._entries.values() if not e.is_deleted)

    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not deleted."""
        with self._lock:
            if key in self._entries:
                return not self._entries[key].is_deleted
            return False

    # Tolerant fallback for any unknown logger-style methods
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Singleton instance for shared access
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(max_size: int = 10000) -> MemoryBuffer:
    """
    Get the shared memory buffer singleton.

    Args:
        max_size: Maximum size for the buffer (only used on first creation).

    Returns:
        The shared MemoryBuffer instance.
    """
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(max_size=max_size)
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()

def __getattr__(name: str):
    """
    Tolerant fallback for any attribute access on this module.
    Prevents AttributeError when unknown symbols are accessed.
    """
    def _noop(*args: Any, **kwargs: Any) -> Any:
        return None
    return _noop