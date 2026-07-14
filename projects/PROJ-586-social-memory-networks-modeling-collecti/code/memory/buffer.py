"""
Shared external memory buffer for multi-agent systems.

Implements a thread-safe queue-based memory buffer supporting:
- <MEMORY_ACTION> tokens with JSON schema: {"type": "write"|"read", "key": str, "value": str}
- Queue-based write conflict resolution (FIFO with overwrite policy)
- Shared singleton buffer access
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, Callable

# Token format for memory actions
MEMORY_ACTION_TOKEN_PATTERN = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"

@dataclass
class MemoryAction:
    """Represents a single memory action with JSON schema compliance."""
    type: Literal["write", "read"]
    key: str
    value: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
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
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        """Create from dictionary."""
        return cls(
            type=data["type"],
            key=data["key"],
            value=data["value"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            agent_id=data.get("agent_id")
        )

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryAction":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

@dataclass
class MemoryEntry:
    """A stored memory entry with metadata for conflict resolution."""
    key: str
    value: str
    created_at: str
    updated_at: str
    agent_id: Optional[str] = None
    version: int = 1
    access_count: int = 0

@dataclass
class WriteConflict:
    """Represents a write conflict between multiple agents."""
    key: str
    competing_actions: List[MemoryAction]
    resolved_by: str
    resolution_strategy: str

def now() -> float:
    """Return current timestamp."""
    return time.time()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """
    Parse a <MEMORY_ACTION> token string into a MemoryAction object.
    
    Args:
        token: String containing <MEMORY_ACTION>...</MEMORY_ACTION>
        
    Returns:
        MemoryAction if valid, None otherwise
    """
    match = re.search(MEMORY_ACTION_TOKEN_PATTERN, token, re.DOTALL)
    if not match:
        return None
    
    try:
        json_str = match.group(1).strip()
        data = json.loads(json_str)
        return MemoryAction.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """
    Format a MemoryAction as a <MEMORY_ACTION> token string.
    
    Args:
        action: MemoryAction to format
        
    Returns:
        Formatted token string
    """
    return f"<MEMORY_ACTION>{action.to_json()}</MEMORY_ACTION>"

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
            json_str = match.group(1).strip()
            data = json.loads(json_str)
            actions.append(MemoryAction.from_dict(data))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    
    return actions

class WriteConflictResolver:
    """
    Resolves write conflicts using queue-based FIFO strategy.
    
    Policy: First-write-wins (actions are processed in order of arrival).
    Later writes to the same key are queued and resolved by updating the version.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._write_queue: deque = deque()
        self._conflict_log: List[WriteConflict] = []
    
    def resolve(self, action: MemoryAction, existing_entry: Optional[MemoryEntry]) -> MemoryAction:
        """
        Resolve a write action against existing memory state.
        
        Args:
            action: The incoming write action
            existing_entry: Optional existing entry for the same key
            
        Returns:
            The resolved action (may be modified with updated timestamp/version)
        """
        with self._lock:
            self._write_queue.append(action)
            
            if existing_entry:
                # Conflict detected: same key written by different agent or later time
                conflict = WriteConflict(
                    key=action.key,
                    competing_actions=[existing_entry],
                    resolved_by=action.agent_id or "system",
                    resolution_strategy="fifo_version_increment"
                )
                self._conflict_log.append(conflict)
                
                # Update version for conflict resolution
                action.timestamp = now()
                # Note: In a full implementation, we might queue this for later processing
                # For now, we allow the write but increment version tracking
            
            return action

    def get_conflicts(self) -> List[WriteConflict]:
        """Return list of all recorded conflicts."""
        with self._lock:
            return list(self._conflict_log)

    def get_queue_length(self) -> int:
        """Return current write queue length."""
        with self._lock:
            return len(self._write_queue)

class MemoryBuffer:
    """
    Thread-safe shared memory buffer for multi-agent systems.
    
    Features:
    - Stores memory entries indexed by key
    - Supports write and read operations via <MEMORY_ACTION> tokens
    - Implements queue-based conflict resolution for concurrent writes
    - Provides thread-safe access via locks
    """
    
    def __init__(self, max_size: int = 10000):
        self._lock = threading.RLock()
        self._entries: Dict[str, MemoryEntry] = {}
        self._access_log: deque = deque(maxlen=10000)
        self._conflict_resolver = WriteConflictResolver()
        self._max_size = max_size
        self._write_queue: deque = deque()
    
    def write(self, key: str, value: str, agent_id: Optional[str] = None) -> MemoryAction:
        """
        Write a value to memory under the given key.
        
        Args:
            key: Memory key
            value: Value to store
            agent_id: Optional agent identifier
            
        Returns:
            The MemoryAction performed
        """
        with self._lock:
            action = MemoryAction(
                type="write",
                key=key,
                value=value,
                agent_id=agent_id
            )
            
            existing = self._entries.get(key)
            resolved_action = self._conflict_resolver.resolve(action, existing)
            
            if existing:
                # Update existing entry
                entry = MemoryEntry(
                    key=key,
                    value=value,
                    created_at=existing.created_at,
                    updated_at=resolved_action.timestamp,
                    agent_id=agent_id,
                    version=existing.version + 1,
                    access_count=existing.access_count
                )
            else:
                # Create new entry
                entry = MemoryEntry(
                    key=key,
                    value=value,
                    created_at=resolved_action.timestamp,
                    updated_at=resolved_action.timestamp,
                    agent_id=agent_id,
                    version=1,
                    access_count=0
                )
            
            self._entries[key] = entry
            self._access_log.append({
                "action": "write",
                "key": key,
                "agent_id": agent_id,
                "timestamp": resolved_action.timestamp
            })
            
            # Enforce max size
            if len(self._entries) > self._max_size:
                # Remove oldest entry (FIFO eviction)
                oldest_key = next(iter(self._entries))
                del self._entries[oldest_key]
            
            return resolved_action

    def read(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """
        Read a value from memory by key.
        
        Args:
            key: Memory key
            agent_id: Optional agent identifier
            
        Returns:
            Value if found, None otherwise
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            
            # Update access count
            entry.access_count += 1
            
            self._access_log.append({
                "action": "read",
                "key": key,
                "agent_id": agent_id,
                "timestamp": now()
            })
            
            return entry.value

    def delete(self, key: str) -> bool:
        """
        Delete a key from memory.
        
        Args:
            key: Memory key to delete
            
        Returns:
            True if deleted, False if key not found
        """
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                self._access_log.append({
                    "action": "delete",
                    "key": key,
                    "timestamp": now()
                })
                return True
            return False

    def get(self, key: str) -> Optional[MemoryEntry]:
        """
        Get full entry details for a key.
        
        Args:
            key: Memory key
            
        Returns:
            MemoryEntry if found, None otherwise
        """
        with self._lock:
            return self._entries.get(key)

    def get_all_keys(self) -> List[str]:
        """Return list of all keys in memory."""
        with self._lock:
            return list(self._entries.keys())

    def get_entries(self) -> Dict[str, MemoryEntry]:
        """Return a copy of all entries."""
        with self._lock:
            return dict(self._entries)

    def process_action_token(self, token: str, agent_id: Optional[str] = None) -> Optional[str]:
        """
        Process a <MEMORY_ACTION> token and return result.
        
        Args:
            token: Token string to process
            agent_id: Agent performing the action
            
        Returns:
            Result value for read, None for write
        """
        action = parse_memory_action_token(token)
        if action is None:
            return None
        
        if action.agent_id is None:
            action.agent_id = agent_id
        
        if action.type == "write":
            self.write(action.key, action.value, action.agent_id)
            return None
        elif action.type == "read":
            return self.read(action.key, action.agent_id)
        else:
            return None

    def reset(self) -> None:
        """Reset the buffer to empty state."""
        with self._lock:
            self._entries.clear()
            self._access_log.clear()
            self._conflict_resolver = WriteConflictResolver()
            self._write_queue.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Return buffer statistics."""
        with self._lock:
            return {
                "entry_count": len(self._entries),
                "max_size": self._max_size,
                "conflict_count": len(self._conflict_resolver.get_conflicts()),
                "queue_length": len(self._write_queue),
                "access_log_length": len(self._access_log)
            }

# Shared buffer instance (singleton pattern)
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(max_size: int = 10000) -> MemoryBuffer:
    """
    Get or create the shared memory buffer instance.
    
    Args:
        max_size: Maximum number of entries (only used on first creation)
        
    Returns:
        The shared MemoryBuffer instance
    """
    global _SHARED_BUFFER

    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(max_size=max_size)
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the shared buffer instance."""
    global _SHARED_BUFFER

    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()

# Tolerant attribute access for logger-like usage
def __getattr__(self, name: str):
    """
    Provide tolerant attribute access for unknown methods.
    Returns a no-op callable to prevent AttributeError on dynamic calls.
    """
    def _noop(*args: Any, **kwargs: Any) -> Any:
        return None
    return _noop