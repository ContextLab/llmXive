"""
Shared external memory buffer with <MEMORY_ACTION> token handling.

Implements a thread-safe, distributed ledger-style memory for multi-agent systems.
Supports parsing, formatting, and executing memory actions (STORE, RETRIEVE, UPDATE, DELETE).
"""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from collections import OrderedDict


class MemoryActionType(str, Enum):
    """Types of memory actions supported by the buffer."""
    STORE = "STORE"
    RETRIEVE = "RETRIEVE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class MemoryAction:
    """Represents a single memory action to be executed or logged."""
    action_type: MemoryActionType
    key: str
    value: Optional[Any] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization."""
        return {
            "action_type": self.action_type.value,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "context": self.context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryAction:
        """Create action from dictionary."""
        return cls(
            action_type=MemoryActionType(data["action_type"]),
            key=data["key"],
            value=data.get("value"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            agent_id=data.get("agent_id"),
            context=data.get("context")
        )


@dataclass
class MemoryEntry:
    """A single entry in the memory buffer with metadata."""
    key: str
    value: Any
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None
    agent_creator: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryEntry:
        """Create entry from dictionary."""
        return cls(**data)


def now() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat()


# Regex pattern for <MEMORY_ACTION> tokens
# Format: <MEMORY_ACTION:TYPE:key:value(optional)>
MEMORY_ACTION_PATTERN = re.compile(
    r'<MEMORY_ACTION:(STORE|RETRIEVE|UPDATE|DELETE):([^:]+)(?::([^>]*))?>'
)


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """
    Parse a <MEMORY_ACTION> token string into a MemoryAction object.
    
    Args:
        token: String in format <MEMORY_ACTION:TYPE:key:value>
        
    Returns:
        MemoryAction object if parsing succeeds, None otherwise.
    """
    if not token or not isinstance(token, str):
        return None
        
    match = MEMORY_ACTION_PATTERN.match(token.strip())
    if not match:
        return None
        
    action_type_str, key, value_str = match.groups()
    
    try:
        action_type = MemoryActionType(action_type_str)
    except ValueError:
        return None
        
    value = None
    if value_str:
        try:
            # Try to parse as JSON first
            value = json.loads(value_str)
        except (json.JSONDecodeError, TypeError):
            # Fall back to string
            value = value_str
            
    return MemoryAction(
        action_type=action_type,
        key=key,
        value=value,
        timestamp=now()
    )


def parse_memory_action(text: str) -> List[MemoryAction]:
    """
    Extract all <MEMORY_ACTION> tokens from a text string.
    
    Args:
        text: Text containing zero or more memory action tokens.
        
    Returns:
        List of parsed MemoryAction objects.
    """
    actions = []
    if not text or not isinstance(text, str):
        return actions
        
    for match in MEMORY_ACTION_PATTERN.finditer(text):
        full_token = match.group(0)
        action = parse_memory_action_token(full_token)
        if action:
            actions.append(action)
            
    return actions


def format_action_token(action: MemoryAction) -> str:
    """
    Format a MemoryAction object back into a <MEMORY_ACTION> token string.
    
    Args:
        action: MemoryAction object to format.
        
    Returns:
        String in format <MEMORY_ACTION:TYPE:key:value>.
    """
    value_str = ""
    if action.value is not None:
        try:
            value_str = f":{json.dumps(action.value, ensure_ascii=False)}"
        except (TypeError, ValueError):
            value_str = f":{str(action.value)}"
            
    return f"<MEMORY_ACTION:{action.action_type.value}:{action.key}{value_str}>"


def parse_action_from_prompt(prompt_text: str) -> List[MemoryAction]:
    """
    Parse memory actions from an agent's prompt text.
    
    This is a convenience wrapper around parse_memory_action that handles
    common prompt formatting variations.
    
    Args:
        prompt_text: The agent's prompt text.
        
    Returns:
        List of MemoryAction objects extracted from the prompt.
    """
    return parse_memory_action(prompt_text)


class MemoryBuffer:
    """
    Thread-safe shared external memory buffer for multi-agent systems.
    
    Implements a distributed ledger-style memory where agents can store,
    retrieve, update, and delete information. Supports <MEMORY_ACTION> token
    parsing and execution.
    
    Thread Safety: All public methods are thread-safe using a reentrant lock.
    """
    
    def __init__(self, max_size: int = 10000, eviction_policy: str = "lru"):
        """
        Initialize the memory buffer.
        
        Args:
            max_size: Maximum number of entries before eviction.
            eviction_policy: Policy for evicting entries ("lru", "fifo", "random").
        """
        self._buffer: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._eviction_policy = eviction_policy
        self._action_log: List[MemoryAction] = []
        self._stats = {
            "total_stores": 0,
            "total_retrieves": 0,
            "total_updates": 0,
            "total_deletes": 0,
            "total_evictions": 0
        }
        
    def reset(self) -> None:
        """Reset the buffer to empty state."""
        with self._lock:
            self._buffer.clear()
            self._action_log.clear()
            self._stats = {
                "total_stores": 0,
                "total_retrieves": 0,
                "total_updates": 0,
                "total_deletes": 0,
                "total_evictions": 0
            }
            
    def _evict_if_needed(self) -> None:
        """Evict entries if buffer exceeds max size."""
        while len(self._buffer) > self._max_size:
            if self._eviction_policy == "lru":
                # Remove least recently used (first item in OrderedDict)
                self._buffer.popitem(last=False)
            elif self._eviction_policy == "fifo":
                # Remove oldest (first item)
                self._buffer.popitem(last=False)
            elif self._eviction_policy == "random":
                import random
                key = random.choice(list(self._buffer.keys()))
                del self._buffer[key]
            else:
                # Default to LRU
                self._buffer.popitem(last=False)
                
            self._stats["total_evictions"] += 1
            
    def store(self, key: str, value: Any, agent_id: Optional[str] = None, 
              tags: Optional[List[str]] = None) -> MemoryEntry:
        """
        Store a value in the memory buffer.
        
        Args:
            key: Unique key for the entry.
            value: Value to store.
            agent_id: ID of the agent storing the value.
            tags: Optional list of tags for categorization.
                
        Returns:
            The created MemoryEntry.
        """
        with self._lock:
            entry = MemoryEntry(
                key=key,
                value=value,
                created_at=now(),
                agent_creator=agent_id,
                tags=tags or []
            )
            
            # If key exists, update it (increment version via updated_at)
            if key in self._buffer:
                existing = self._buffer[key]
                existing.value = value
                existing.updated_at = now()
                existing.agent_creator = agent_id or existing.agent_creator
                existing.tags = tags or existing.tags
                self._buffer.move_to_end(key)
            else:
                self._buffer[key] = entry
                self._evict_if_needed()
                
            self._stats["total_stores"] += 1
            
            # Log the action
            action = MemoryAction(
                action_type=MemoryActionType.STORE,
                key=key,
                value=value,
                agent_id=agent_id
            )
            self._action_log.append(action)
            
            return entry
            
    def retrieve(self, key: str, agent_id: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve a value from the memory buffer.
        
        Args:
            key: Key of the entry to retrieve.
            agent_id: ID of the agent requesting the value.
                
        Returns:
            The value if found, None otherwise.
        """
        with self._lock:
            if key not in self._buffer:
                return None
                
            entry = self._buffer[key]
            entry.access_count += 1
            entry.last_accessed = now()
            self._buffer.move_to_end(key)
            
            self._stats["total_retrieves"] += 1
            
            # Log the action
            action = MemoryAction(
                action_type=MemoryActionType.RETRIEVE,
                key=key,
                value=entry.value,
                agent_id=agent_id
            )
            self._action_log.append(action)
            
            return entry.value
            
    def update(self, key: str, value: Any, agent_id: Optional[str] = None) -> bool:
        """
        Update an existing entry in the memory buffer.
        
        Args:
            key: Key of the entry to update.
            value: New value to store.
            agent_id: ID of the agent performing the update.
                
        Returns:
            True if update succeeded, False if key not found.
        """
        with self._lock:
            if key not in self._buffer:
                return False
                
            entry = self._buffer[key]
            entry.value = value
            entry.updated_at = now()
            entry.agent_creator = agent_id or entry.agent_creator
            self._buffer.move_to_end(key)
            
            self._stats["total_updates"] += 1
            
            # Log the action
            action = MemoryAction(
                action_type=MemoryActionType.UPDATE,
                key=key,
                value=value,
                agent_id=agent_id
            )
            self._action_log.append(action)
            
            return True
            
    def delete(self, key: str, agent_id: Optional[str] = None) -> bool:
        """
        Delete an entry from the memory buffer.
        
        Args:
            key: Key of the entry to delete.
            agent_id: ID of the agent performing the deletion.
                
        Returns:
            True if deletion succeeded, False if key not found.
        """
        with self._lock:
            if key not in self._buffer:
                return False
                
            del self._buffer[key]
            self._stats["total_deletes"] += 1
            
            # Log the action
            action = MemoryAction(
                action_type=MemoryActionType.DELETE,
                key=key,
                agent_id=agent_id
            )
            self._action_log.append(action)
            
            return True
            
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get a value from the buffer (alias for retrieve).
        
        Args:
            key: Key to look up.
            default: Value to return if key not found.
                
        Returns:
            The value if found, default otherwise.
        """
        result = self.retrieve(key)
        return result if result is not None else default
            
    def exists(self, key: str) -> bool:
        """Check if a key exists in the buffer."""
        with self._lock:
            return key in self._buffer
            
    def keys(self) -> List[str]:
        """Return list of all keys in the buffer."""
        with self._lock:
            return list(self._buffer.keys())
            
    def items(self) -> List[tuple]:
        """Return list of (key, value) pairs in the buffer."""
        with self._lock:
            return [(k, v.value) for k, v in self._buffer.items()]
            
    def clear(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._buffer.clear()
            
    def size(self) -> int:
        """Return current number of entries in the buffer."""
        with self._lock:
            return len(self._buffer)
            
    def get_stats(self) -> Dict[str, Any]:
        """Return buffer statistics."""
        with self._lock:
            return {
                **self._stats,
                "current_size": len(self._buffer),
                "max_size": self._max_size,
                "eviction_policy": self._eviction_policy
            }
            
    def execute_action(self, action: Union[str, MemoryAction]) -> Optional[Any]:
        """
        Execute a memory action from a token string or MemoryAction object.
        
        Args:
            action: Either a <MEMORY_ACTION> token string or a MemoryAction object.
                
        Returns:
            Result of the action (value for RETRIEVE, bool for others, None for others).
        """
        if isinstance(action, str):
            parsed = parse_memory_action_token(action)
            if not parsed:
                return None
            action = parsed
            
        if action.action_type == MemoryActionType.STORE:
            self.store(action.key, action.value, action.agent_id)
            return None
        elif action.action_type == MemoryActionType.RETRIEVE:
            return self.retrieve(action.key, action.agent_id)
        elif action.action_type == MemoryActionType.UPDATE:
            return self.update(action.key, action.value, action.agent_id)
        elif action.action_type == MemoryActionType.DELETE:
            return self.delete(action.key, action.agent_id)
            
        return None
            
    def process_text(self, text: str, agent_id: Optional[str] = None) -> List[Any]:
        """
        Process a text string containing <MEMORY_ACTION> tokens.
        
        Args:
            text: Text containing memory action tokens.
            agent_id: Agent ID to associate with the actions.
                
        Returns:
            List of results from executing each action.
        """
        actions = parse_memory_action(text)
        results = []
        for action in actions:
            action.agent_id = agent_id
            results.append(self.execute_action(action))
        return results
            
    def to_dict(self) -> Dict[str, Any]:
        """Export buffer state to dictionary."""
        with self._lock:
            return {
                "entries": {k: v.to_dict() for k, v in self._buffer.items()},
                "stats": self.get_stats(),
                "action_log": [a.to_dict() for a in self._action_log[-100:]]  # Last 100 actions
            }
            
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryBuffer:
        """Load buffer state from dictionary."""
        buffer = cls(
            max_size=data.get("max_size", 10000),
            eviction_policy=data.get("eviction_policy", "lru")
        )
        with buffer._lock:
            buffer._buffer = OrderedDict()
            for key, entry_data in data.get("entries", {}).items():
                buffer._buffer[key] = MemoryEntry.from_dict(entry_data)
            buffer._stats = data.get("stats", buffer._stats)
        return buffer


# Global shared buffer instance
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer(max_size: int = 10000, eviction_policy: str = "lru") -> MemoryBuffer:
    """
    Get or create the global shared memory buffer instance.
    
    Args:
        max_size: Maximum size for the buffer (only used on first creation).
        eviction_policy: Eviction policy (only used on first creation).
            
    Returns:
        The shared MemoryBuffer instance.
    """
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(max_size=max_size, eviction_policy=eviction_policy)
        return _SHARED_BUFFER


def reset_shared_buffer() -> None:
    """Reset the global shared buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()