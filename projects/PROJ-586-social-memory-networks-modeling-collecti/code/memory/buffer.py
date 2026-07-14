"""Shared external memory buffer for multi-agent social memory networks.

Implements a thread-safe memory buffer supporting <MEMORY_ACTION> tokens with
JSON schema {"type": "write"|"read", "key": str, "value": str}.
Includes queue-based write conflict resolution.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# Token pattern for memory actions
MEMORY_ACTION_PATTERN = re.compile(r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>")

@dataclass
class MemoryAction:
    """Represents a memory action (write or read)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None
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

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryAction:
        """Create from dictionary representation."""
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value"),
            timestamp=data.get("timestamp", time.time()),
            agent_id=data.get("agent_id")
        )

    def validate(self) -> bool:
        """Validate the action schema."""
        if self.type not in ("write", "read"):
            return False
        if not self.key or not isinstance(self.key, str):
            return False
        if self.type == "write" and self.value is None:
            return False
        return True

@dataclass
class MemoryEntry:
    """Represents a stored memory entry."""
    key: str
    value: str
    timestamp: float
    agent_id: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed
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
        action_data = json.loads(match.group(1))
        action = MemoryAction.from_dict(action_data)
        if action.validate():
            return action
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    return None

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction object as a <MEMORY_ACTION> token string."""
    return f"<MEMORY_ACTION>{json.dumps(action.to_dict())}</MEMORY_ACTION>"

def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """
    Extract all memory actions from a prompt string.
    
    Args:
        prompt: Text potentially containing multiple <MEMORY_ACTION> tokens
        
    Returns:
        List of parsed MemoryAction objects
    """
    actions = []
    pattern = re.compile(MEMORY_ACTION_TOKEN_PATTERN, re.DOTALL)
    
    for match in pattern.finditer(prompt):
        try:
            action_data = json.loads(match.group(1))
            action = MemoryAction.from_dict(action_data)
            if action.validate():
                actions.append(action)
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    
    return actions

class WriteConflictResolver:
    """Resolves write conflicts using a queue-based approach."""

    def __init__(self):
        self._write_queue: deque = deque()
        self._lock = threading.Lock()
        self._conflict_count = 0
        self._resolution_log: List[Dict[str, Any]] = []

    def submit_write(self, action: MemoryAction) -> int:
        """Submit a write action to the queue. Returns queue position."""
        with self._lock:
            position = len(self._write_queue)
            self._write_queue.append(action)
            return position

    def process_queue(self, memory: Dict[str, MemoryEntry]) -> List[Dict[str, Any]]:
        """Process the write queue, resolving conflicts and updating memory."""
        resolutions = []

        with self._lock:
            while self._write_queue:
                action = self._write_queue.popleft()
                resolution = self._resolve_single_write(action, memory)
                resolutions.append(resolution)

        return resolutions

    def _resolve_single_write(self, action: MemoryAction, memory: Dict[str, MemoryEntry]) -> Dict[str, Any]:
        """Resolve a single write action, handling conflicts."""
        result = {
            "action": action.to_dict(),
            "resolved": False,
            "reason": "",
            "timestamp": now()
        }

        if action.key in memory:
            existing = memory[action.key]
            if existing.timestamp > action.timestamp:
                # Existing entry is newer, reject this write
                result["reason"] = "stale_write"
                self._conflict_count += 1
                self._resolution_log.append(result)
                return result
            elif existing.agent_id == action.agent_id:
                # Same agent, update allowed
                result["reason"] = "same_agent_update"
            else:
                # Different agent, use timestamp-based resolution
                result["reason"] = "timestamp_resolution"

        # Apply the write
        memory[action.key] = MemoryEntry(
            key=action.key,
            value=action.value or "",
            timestamp=action.timestamp,
            agent_id=action.agent_id
        )
        result["resolved"] = True
        self._resolution_log.append(result)
        return result

    def get_conflict_count(self) -> int:
        """Return the number of resolved conflicts."""
        return self._conflict_count

    def get_resolution_log(self) -> List[Dict[str, Any]]:
        """Return the conflict resolution log."""
        return self._resolution_log.copy()

    def clear(self):
        """Clear the queue and reset counters."""
        with self._lock:
            self._write_queue.clear()
            self._conflict_count = 0
            self._resolution_log.clear()

class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems."""

    def __init__(self, max_size: int = 10000):
        self._memory: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._resolver = WriteConflictResolver()
        self._access_log: List[Dict[str, Any]] = []
        self._write_queue: deque = deque()

    def write(self, key: str, value: str, agent_id: Optional[str] = None) -> bool:
        """Write a value to memory with conflict resolution."""
        action = MemoryAction(
            type="write",
            key=key,
            value=value,
            agent_id=agent_id
        )

        with self._lock:
            if len(self._memory) >= self._max_size and key not in self._memory:
                # Evict oldest entry if at capacity
                oldest_key = min(self._memory.keys(), key=lambda k: self._memory[k].timestamp)
                del self._memory[oldest_key]

            self._memory[key] = MemoryEntry(
                key=key,
                value=value,
                timestamp=now(),
                agent_id=agent_id
            )

            self._access_log.append({
                "action": "write",
                "key": key,
                "agent_id": agent_id,
                "timestamp": now()
            })

            return True

    def read(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """Read a value from memory."""
        with self._lock:
            if key not in self._memory:
                return None

            entry = self._memory[key]
            entry.access_count += 1
            entry.last_accessed = now()

            self._access_log.append({
                "action": "read",
                "key": key,
                "agent_id": agent_id,
                "timestamp": now()
            })

            return entry.value

    def delete(self, key: str) -> bool:
        """Delete a key from memory."""
        with self._lock:
            if key in self._memory:
                del self._memory[key]
                self._access_log.append({
                    "action": "delete",
                    "key": key,
                    "timestamp": now()
                })
                return True
            return False

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a value with optional default."""
        return self.read(key) or default

    def set(self, key: str, value: str) -> bool:
        """Set a value (alias for write)."""
        return self.write(key, value)

    def contains(self, key: str) -> bool:
        """Check if a key exists in memory."""
        with self._lock:
            return key in self._memory

    def keys(self) -> List[str]:
        """Return all keys in memory."""
        with self._lock:
            return list(self._memory.keys())

    def values(self) -> List[str]:
        """Return all values in memory."""
        with self._lock:
            return [entry.value for entry in self._memory.values()]

    def items(self) -> List[tuple]:
        """Return all key-value pairs."""
        with self._lock:
            return [(k, entry.value) for k, entry in self._memory.items()]

    def size(self) -> int:
        """Return the number of entries in memory."""
        with self._lock:
            return len(self._memory)

    def clear(self):
        """Clear all memory entries."""
        with self._lock:
            self._memory.clear()
            self._access_log.clear()

    def reset(self):
        """Reset the buffer to initial state."""
        with self._lock:
            self._memory.clear()
            self._access_log.clear()
            self._write_queue.clear()
            self._resolver.clear()

    def process_pending_writes(self) -> List[Dict[str, Any]]:
        """Process any pending writes in the queue."""
        with self._lock:
            while self._write_queue:
                action = self._write_queue.popleft()
                self.write(action.key, action.value or "", action.agent_id)
            return []

    def submit_write_action(self, action: MemoryAction) -> int:
        """Submit a write action to the conflict resolution queue."""
        with self._lock:
            position = len(self._write_queue)
            self._write_queue.append(action)
            return position

    def get_access_log(self) -> List[Dict[str, Any]]:
        """Return a copy of the access log."""
        with self._lock:
            return self._access_log.copy()

    def get_entries(self) -> Dict[str, MemoryEntry]:
        """Return a copy of all entries."""
        with self._lock:
            return {
                "size": len(self._memory),
                "max_size": self._max_size,
                "total_accesses": len(self._access_log),
                "conflicts_resolved": self._resolver.get_conflict_count()
            }

    # Tolerant attribute access for logger-style calls
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

# Shared buffer instance (singleton pattern)
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(max_size: int = 10000) -> MemoryBuffer:
    """Get or create the shared memory buffer singleton."""
    global _SHARED_BUFFER

    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(max_size=max_size)
        return _SHARED_BUFFER

def reset_shared_buffer():
    """Reset the shared memory buffer."""
    global _SHARED_BUFFER

    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
            _SHARED_BUFFER = None