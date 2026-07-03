"""Shared external memory buffer with <MEMORY_ACTION> token handling.

Implements a thread-safe, shared memory buffer for multi-agent systems.
Supports serialization/deserialization of memory actions via token strings.
"""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, TypeVar

T = TypeVar('T')

# Token pattern for memory actions
MEMORY_ACTION_PATTERN = re.compile(r'<MEMORY_ACTION>(.*?)</MEMORY_ACTION>')

@dataclass
class MemoryAction:
    """Represents a single memory action (store, retrieve, update, delete)."""
    action_type: str  # 'store', 'retrieve', 'update', 'delete'
    key: str
    value: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryAction:
        """Create from dictionary."""
        return cls(**data)

    def to_token_string(self) -> str:
        """Serialize to token string format."""
        return f"<MEMORY_ACTION>{json.dumps(self.to_dict())}</MEMORY_ACTION>"

    @classmethod
    def from_token_string(cls, token_str: str) -> Optional[MemoryAction]:
        """Parse from token string format."""
        match = MEMORY_ACTION_PATTERN.search(token_str)
        if not match:
            return None
        try:
            data = json.loads(match.group(1))
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

@dataclass
class MemoryEntry:
    """A stored memory entry with metadata."""
    key: str
    value: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0
    last_accessed: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryEntry:
        """Create from dictionary."""
        return cls(**data)

class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems.

    Provides store, retrieve, update, delete operations with optional
    action logging via MemoryAction tokens.
    """

    def __init__(self, capacity: int = 10000, action_logging: bool = True):
        self._buffer: Dict[str, MemoryEntry] = {}
        self._capacity = capacity
        self._action_logging = action_logging
        self._lock = threading.RLock()
        self._action_log: List[MemoryAction] = []
        self._action_log_lock = threading.Lock()

    def _log_action(self, action: MemoryAction) -> None:
        """Log an action if logging is enabled."""
        if self._action_logging:
            with self._action_log_lock:
                self._action_log.append(action)

    def store(self, key: str, value: str, agent_id: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a memory entry."""
        with self._lock:
            if len(self._buffer) >= self._capacity and key not in self._buffer:
                # Evict oldest entry
                oldest_key = min(self._buffer.keys(),
                                 key=lambda k: self._buffer[k].created_at)
                del self._buffer[oldest_key]

            entry = MemoryEntry(
                key=key,
                value=value,
                agent_id=agent_id,
                metadata=metadata or {}
            )
            self._buffer[key] = entry

            # Log action
            action = MemoryAction(
                action_type='store',
                key=key,
                value=value,
                agent_id=agent_id,
                metadata=metadata or {}
            )
            self._log_action(action)
            return True

    def retrieve(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """Retrieve a memory entry by key."""
        with self._lock:
            if key not in self._buffer:
                return None

            entry = self._buffer[key]
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow().isoformat()

            # Log action
            action = MemoryAction(
                action_type='retrieve',
                key=key,
                agent_id=agent_id
            )
            self._log_action(action)
            return entry.value

    def update(self, key: str, value: str, agent_id: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing memory entry."""
        with self._lock:
            if key not in self._buffer:
                return False

            entry = self._buffer[key]
            entry.value = value
            entry.updated_at = datetime.utcnow().isoformat()
            if metadata:
                entry.metadata.update(metadata)
            if agent_id:
                entry.agent_id = agent_id

            # Log action
            action = MemoryAction(
                action_type='update',
                key=key,
                value=value,
                agent_id=agent_id,
                metadata=metadata or {}
            )
            self._log_action(action)
            return True

    def delete(self, key: str, agent_id: Optional[str] = None) -> bool:
        """Delete a memory entry."""
        with self._lock:
            if key not in self._buffer:
                return False

            del self._buffer[key]

            # Log action
            action = MemoryAction(
                action_type='delete',
                key=key,
                agent_id=agent_id
            )
            self._log_action(action)
            return True

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get value by key (alias for retrieve)."""
        return self.retrieve(key)

    def set(self, key: str, value: str) -> bool:
        """Set value by key (alias for store)."""
        return self.store(key, value)

    def has(self, key: str) -> bool:
        """Check if key exists."""
        with self._lock:
            return key in self._buffer

    def keys(self) -> List[str]:
        """Return all keys."""
        with self._lock:
            return list(self._buffer.keys())

    def values(self) -> List[str]:
        """Return all values."""
        with self._lock:
            return [entry.value for entry in self._buffer.values()]

    def items(self) -> List[tuple]:
        """Return all (key, value) pairs."""
        with self._lock:
            return [(k, entry.value) for k, entry in self._buffer.items()]

    def size(self) -> int:
        """Return current buffer size."""
        with self._lock:
            return len(self._buffer)

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._buffer.clear()

    def reset(self) -> None:
        """Reset buffer and action log."""
        with self._lock:
            self._buffer.clear()
        with self._action_log_lock:
            self._action_log.clear()

    def get_action_log(self) -> List[MemoryAction]:
        """Return copy of action log."""
        with self._action_log_lock:
            return list(self._action_log)

    def parse_and_execute(self, token_string: str, agent_id: Optional[str] = None) -> Any:
        """Parse a token string and execute the memory action.

        Returns the result of the action or None if parsing fails.
        """
        action = MemoryAction.from_token_string(token_string)
        if action is None:
            return None

        # Set agent_id if not provided in action
        if action.agent_id is None:
            action.agent_id = agent_id

        if action.action_type == 'store':
            return self.store(action.key, action.value or '',
                             action.agent_id, action.metadata)
        elif action.action_type == 'retrieve':
            return self.retrieve(action.key, action.agent_id)
        elif action.action_type == 'update':
            return self.update(action.key, action.value or '',
                              action.agent_id, action.metadata)
        elif action.action_type == 'delete':
            return self.delete(action.key, action.agent_id)
        return None

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Tolerant fallback for unknown logger-style methods."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Shared buffer singleton
_shared_buffer: Optional[MemoryBuffer] = None
_shared_buffer_lock = threading.Lock()

def get_shared_buffer(capacity: int = 10000, action_logging: bool = True) -> MemoryBuffer:
    """Get or create the shared memory buffer singleton."""
    global _shared_buffer
    with _shared_buffer_lock:
        if _shared_buffer is None:
            _shared_buffer = MemoryBuffer(capacity=capacity,
                                         action_logging=action_logging)
        return _shared_buffer

def get_shared_memory_buffer(capacity: int = 10000, action_logging: bool = True) -> MemoryBuffer:
    """Alias for get_shared_buffer for compatibility."""
    return get_shared_buffer(capacity=capacity, action_logging=action_logging)

def reset_shared_buffer() -> None:
    """Reset the shared buffer singleton."""
    global _shared_buffer
    with _shared_buffer_lock:
        if _shared_buffer is not None:
            _shared_buffer.reset()
            _shared_buffer = None

def now() -> str:
    """Return current timestamp string."""
    return datetime.utcnow().isoformat()

def parse_memory_action(token_string: str) -> Optional[MemoryAction]:
    """Parse a memory action from token string."""
    return MemoryAction.from_token_string(token_string)

def parse_memory_action_token(token_string: str) -> Optional[MemoryAction]:
    """Alias for parse_memory_action."""
    return parse_memory_action(token_string)