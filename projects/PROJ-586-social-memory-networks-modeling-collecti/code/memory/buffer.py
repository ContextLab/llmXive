"""
Shared external memory buffer with <MEMORY_ACTION> token handling.

Implements a thread-safe, singleton shared memory buffer for multi-agent
transactive memory systems. Supports <MEMORY_ACTION> token parsing and
various memory operations (store, update, retrieve).
"""

import threading
import time
import re
from dataclasses import dataclass, field
from typing import List, Any, Optional, Callable, Dict, Union
from pathlib import Path
import json
import logging

# Configure logger for this module
_logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Represents a single entry in the shared memory buffer."""
    entry_id: str
    content: Any
    agent_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        return {
            'entry_id': self.entry_id,
            'content': self.content,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed,
            'tags': self.tags,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create entry from dictionary."""
        return cls(
            entry_id=data['entry_id'],
            content=data['content'],
            agent_id=data.get('agent_id'),
            timestamp=data.get('timestamp', time.time()),
            access_count=data.get('access_count', 0),
            last_accessed=data.get('last_accessed', time.time()),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


def parse_memory_action(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse <MEMORY_ACTION> tokens from text.

    Supports formats:
    - <MEMORY_ACTION:store:key=value>
    - <MEMORY_ACTION:update:key=value>
    - <MEMORY_ACTION:retrieve:key>
    - <MEMORY_ACTION:delete:key>

    Args:
        text: String potentially containing memory action tokens

    Returns:
        Dictionary with action type, key, and value if found, None otherwise
    """
    # Pattern to match <MEMORY_ACTION:action:key=value> or <MEMORY_ACTION:action:key>
    pattern = r'<MEMORY_ACTION:(store|update|retrieve|delete):([^>:]+)(?:=([^>]+))?>'
    match = re.search(pattern, text)

    if match:
        action_type = match.group(1)
        key = match.group(2)
        value = match.group(3) if match.group(3) else None

        return {
            'action': action_type,
            'key': key,
            'value': value,
            'raw_match': match.group(0)
        }

    return None


class MemoryBuffer:
    """
    Thread-safe shared memory buffer for multi-agent systems.

    Implements a singleton pattern to ensure all agents access the same
    memory buffer. Supports various memory operations and token-based
    memory actions.
    """

    _instance: Optional['MemoryBuffer'] = None
    _lock = threading.Lock()
    _init_lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the memory buffer (only once due to singleton)."""
        if self._initialized:
            return

        with self._lock:
            self._entries: Dict[str, MemoryEntry] = {}
            self._callbacks: Dict[str, List[Callable]] = {
                'store': [],
                'update': [],
                'retrieve': [],
                'delete': []
            }
            self._entry_counter = 0
            self._lock = threading.RLock()
            self._initialized = True
            _logger.debug("MemoryBuffer initialized")

    def store(self, key: str, value: Any, agent_id: Optional[str] = None,
              tags: Optional[List[str]] = None, metadata: Optional[Dict] = None) -> MemoryEntry:
        """
        Store a value in the memory buffer.

        Args:
            key: Unique identifier for the entry
            value: Content to store
            agent_id: ID of the agent storing the value
            tags: Optional tags for categorization
            metadata: Optional metadata dictionary

        Returns:
            The created MemoryEntry
        """
        with self._lock:
            entry_id = f"mem_{self._entry_counter}"
            self._entry_counter += 1

            entry = MemoryEntry(
                entry_id=entry_id,
                content=value,
                agent_id=agent_id,
                tags=tags or [],
                metadata=metadata or {}
            )

            self._entries[key] = entry

            # Trigger callbacks
            for callback in self._callbacks['store']:
                try:
                    callback('store', key, entry)
                except Exception as e:
                    _logger.warning(f"Store callback failed: {e}")

            _logger.debug(f"Stored entry {key} -> {entry_id}")
            return entry

    def update(self, key: str, value: Any, agent_id: Optional[str] = None,
               tags: Optional[List[str]] = None, metadata: Optional[Dict] = None) -> Optional[MemoryEntry]:
        """
        Update an existing entry in the memory buffer.

        Args:
            key: Identifier of the entry to update
            value: New content value
            agent_id: ID of the agent performing the update
            tags: Optional new tags (replaces existing)
            metadata: Optional new metadata (replaces existing)

        Returns:
            Updated MemoryEntry or None if key doesn't exist
        """
        with self._lock:
            if key not in self._entries:
                _logger.warning(f"Update failed: key {key} not found")
                return None

            entry = self._entries[key]
            entry.content = value
            entry.agent_id = agent_id or entry.agent_id
            if tags is not None:
                entry.tags = tags
            if metadata is not None:
                entry.metadata = metadata
            entry.last_accessed = time.time()
            entry.access_count += 1

            # Trigger callbacks
            for callback in self._callbacks['update']:
                try:
                    callback('update', key, entry)
                except Exception as e:
                    _logger.warning(f"Update callback failed: {e}")

            _logger.debug(f"Updated entry {key}")
            return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """
        Retrieve an entry from the memory buffer.

        Args:
            key: Identifier of the entry to retrieve

        Returns:
            MemoryEntry if found, None otherwise
        """
        with self._lock:
            if key not in self._entries:
                _logger.debug(f"Retrieve failed: key {key} not found")
                return None

            entry = self._entries[key]
            entry.last_accessed = time.time()
            entry.access_count += 1

            # Trigger callbacks
            for callback in self._callbacks['retrieve']:
                try:
                    callback('retrieve', key, entry)
                except Exception as e:
                    _logger.warning(f"Retrieve callback failed: {e}")

            _logger.debug(f"Retrieved entry {key}")
            return entry

    def delete(self, key: str) -> bool:
        """
        Delete an entry from the memory buffer.

        Args:
            key: Identifier of the entry to delete

        Returns:
            True if deleted, False if key didn't exist
        """
        with self._lock:
            if key not in self._entries:
                _logger.debug(f"Delete failed: key {key} not found")
                return False

            del self._entries[key]

            # Trigger callbacks
            for callback in self._callbacks['delete']:
                try:
                    callback('delete', key, None)
                except Exception as e:
                    _logger.warning(f"Delete callback failed: {e}")

            _logger.debug(f"Deleted entry {key}")
            return True

    def reset(self) -> None:
        """Clear all entries from the memory buffer."""
        with self._lock:
            self._entries.clear()
            self._entry_counter = 0
            _logger.info("MemoryBuffer reset")

    def get_all_entries(self) -> List[MemoryEntry]:
        """Get all entries in the buffer."""
        with self._lock:
            return list(self._entries.values())

    def get_entry_count(self) -> int:
        """Get the number of entries in the buffer."""
        with self._lock:
            return len(self._entries)

    def exists(self, key: str) -> bool:
        """Check if a key exists in the buffer."""
        with self._lock:
            return key in self._entries

    def register_callback(self, action: str, callback: Callable) -> None:
        """
        Register a callback for a specific memory action.

        Args:
            action: One of 'store', 'update', 'retrieve', 'delete'
            callback: Function to call when action occurs
        """
        if action not in self._callbacks:
            raise ValueError(f"Invalid action: {action}")

        with self._lock:
            self._callbacks[action].append(callback)
            _logger.debug(f"Registered callback for {action}")

    def process_token(self, text: str, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Process a <MEMORY_ACTION> token in text.

        Args:
            text: Text containing the token
            agent_id: ID of the agent performing the action

        Returns:
            Result dictionary with action details, or None if no token found
        """
        parsed = parse_memory_action(text)
        if not parsed:
            return None

        action_type = parsed['action']
        key = parsed['key']
        value = parsed['value']

        result = {
            'action': action_type,
            'key': key,
            'success': False,
            'entry': None
        }

        if action_type == 'store' and value is not None:
            entry = self.store(key, value, agent_id)
            result['success'] = True
            result['entry'] = entry.to_dict()
        elif action_type == 'update' and value is not None:
            entry = self.update(key, value, agent_id)
            result['success'] = entry is not None
            result['entry'] = entry.to_dict() if entry else None
        elif action_type == 'retrieve':
            entry = self.retrieve(key)
            result['success'] = entry is not None
            result['entry'] = entry.to_dict() if entry else None
        elif action_type == 'delete':
            result['success'] = self.delete(key)

        return result

    def __getattr__(self, name: str) -> Callable:
        """
        Fallback for unknown attributes to support logger-style calls.
        Returns a no-op callable for any unknown method name.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

    def __len__(self) -> int:
        """Return the number of entries in the buffer."""
        return self.get_entry_count()

    def __contains__(self, key: str) -> bool:
        """Check if key is in buffer."""
        return self.exists(key)

    def __str__(self) -> str:
        """String representation of the buffer."""
        return f"MemoryBuffer(entries={len(self._entries)})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"MemoryBuffer(entry_count={len(self._entries)}, entry_ids={list(self._entries.keys())[:5]}...)"


# Singleton instance management
_shared_buffer_instance: Optional[MemoryBuffer] = None


def get_shared_memory_buffer() -> MemoryBuffer:
    """
    Get the singleton shared memory buffer instance.

    Returns:
        The shared MemoryBuffer instance
    """
    global _shared_buffer_instance
    if _shared_buffer_instance is None:
        _shared_buffer_instance = MemoryBuffer()
    return _shared_buffer_instance


def reset_shared_memory_buffer() -> None:
    """Reset the shared memory buffer (clear all entries)."""
    buffer = get_shared_memory_buffer()
    buffer.reset()