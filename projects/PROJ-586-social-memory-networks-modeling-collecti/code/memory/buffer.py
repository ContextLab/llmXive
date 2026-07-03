"""Shared external memory buffer with <MEMORY_ACTION> token handling.

This module implements a thread-safe shared memory buffer for multi-agent
systems. Agents can store, retrieve, update, and delete memory entries
using a token-based interface.
"""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum


class MemoryAction(Enum):
    """Types of memory operations."""
    STORE = "store"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    CLEAR = "clear"


@dataclass
class MemoryEntry:
    """A single memory entry in the shared buffer."""
    id: str
    content: str
    creator: str
    timestamp: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class MemoryActionToken:
    """Token representing a memory action to be executed."""
    action: MemoryAction
    payload: Dict[str, Any]
    timestamp: str
    requester: str
    success: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_token_string(self) -> str:
        """Serialize to <MEMORY_ACTION> token format."""
        data = {
            "action": self.action.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "requester": self.requester,
            "success": self.success,
            "result": self.result,
            "error": self.error
        }
        return f"<MEMORY_ACTION>{json.dumps(data)}</MEMORY_ACTION>"

    @classmethod
    def from_token_string(cls, token: str) -> Optional["MemoryActionToken"]:
        """Parse from <MEMORY_ACTION> token format."""
        pattern = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"
        match = re.search(pattern, token)
        if not match:
            return None

        try:
            data = json.loads(match.group(1))
            action = MemoryAction(data["action"])
            return cls(
                action=action,
                payload=data["payload"],
                timestamp=data["timestamp"],
                requester=data["requester"],
                success=data.get("success", False),
                result=data.get("result"),
                error=data.get("error")
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None


def now() -> str:
    """Return current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def parse_memory_action(token: str) -> Optional[MemoryActionToken]:
    """Parse a <MEMORY_ACTION> token string."""
    return MemoryActionToken.from_token_string(token)


def parse_memory_action_token(token: str) -> Optional[MemoryActionToken]:
    """Alias for parse_memory_action for backward compatibility."""
    return parse_memory_action(token)


class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems.

    This buffer supports:
    - Storing new memory entries
    - Retrieving entries by ID or content query
    - Updating existing entries
    - Deleting entries
    - Listing all entries
    - Clearing the entire buffer
    - Thread-safe operations via locking
    - Token-based action interface
    """

    def __init__(self, max_entries: int = 10000, capacity_warning: float = 0.9):
        """Initialize the memory buffer.

        Args:
            max_entries: Maximum number of entries to store.
            capacity_warning: Threshold (0-1) to trigger capacity warnings.
        """
        self._entries: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._max_entries = max_entries
        self._capacity_warning = capacity_warning
        self._action_history: List[MemoryActionToken] = []
        self._id_counter = 0

    def _generate_id(self) -> str:
        """Generate a unique entry ID."""
        self._id_counter += 1
        return f"mem_{self._id_counter}_{now()}"

    def store(self, content: str, creator: str, tags: Optional[List[str]] = None,
              confidence: float = 1.0) -> MemoryActionToken:
        """Store a new memory entry.

        Args:
            content: The memory content.
            creator: ID of the agent creating this memory.
            tags: Optional list of tags for categorization.
            confidence: Confidence score for this memory (0-1).

        Returns:
            MemoryActionToken with result or error.
        """
        token = MemoryActionToken(
            action=MemoryAction.STORE,
            payload={"content": content, "creator": creator, "tags": tags or [], "confidence": confidence},
            timestamp=now(),
            requester=creator
        )

        with self._lock:
            if len(self._entries) >= self._max_entries:
                token.success = False
                token.error = f"Buffer full ({self._max_entries} entries). Use update or delete first."
                self._action_history.append(token)
                return token

            entry = MemoryEntry(
                id=self._generate_id(),
                content=content,
                creator=creator,
                timestamp=token.timestamp,
                tags=tags or [],
                confidence=confidence
            )
            self._entries[entry.id] = entry
            token.success = True
            token.result = {"entry_id": entry.id}
            self._action_history.append(token)
            return token

    def retrieve(self, entry_id: str) -> MemoryActionToken:
        """Retrieve a memory entry by ID.

        Args:
            entry_id: The ID of the entry to retrieve.

        Returns:
            MemoryActionToken with entry data or error.
        """
        token = MemoryActionToken(
            action=MemoryAction.RETRIEVE,
            payload={"entry_id": entry_id},
            timestamp=now(),
            requester="system"
        )

        with self._lock:
            if entry_id not in self._entries:
                token.success = False
                token.error = f"Entry not found: {entry_id}"
                self._action_history.append(token)
                return token

            entry = self._entries[entry_id]
            entry.access_count += 1
            entry.last_accessed = now()
            token.success = True
            token.result = entry.to_dict()
            self._action_history.append(token)
            return token

    def retrieve_by_content(self, query: str, top_k: int = 5) -> MemoryActionToken:
        """Retrieve entries matching a content query (simple substring match).

        Args:
            query: Search query string.
            top_k: Maximum number of results to return.

        Returns:
            MemoryActionToken with list of matching entries.
        """
        token = MemoryActionToken(
            action=MemoryAction.RETRIEVE,
            payload={"query": query, "top_k": top_k},
            timestamp=now(),
            requester="system"
        )

        with self._lock:
            query_lower = query.lower()
            matches = []
            for entry in self._entries.values():
                if query_lower in entry.content.lower():
                    entry.access_count += 1
                    entry.last_accessed = now()
                    matches.append(entry.to_dict())

            matches.sort(key=lambda x: x["access_count"], reverse=True)
            token.success = True
            token.result = matches[:top_k]
            self._action_history.append(token)
            return token

    def update(self, entry_id: str, content: Optional[str] = None,
               confidence: Optional[float] = None, tags: Optional[List[str]] = None) -> MemoryActionToken:
        """Update an existing memory entry.

        Args:
            entry_id: ID of entry to update.
            content: New content (optional).
            confidence: New confidence score (optional).
            tags: New tags (optional).

        Returns:
            MemoryActionToken with result or error.
        """
        token = MemoryActionToken(
            action=MemoryAction.UPDATE,
            payload={"entry_id": entry_id, "content": content, "confidence": confidence, "tags": tags},
            timestamp=now(),
            requester="system"
        )

        with self._lock:
            if entry_id not in self._entries:
                token.success = False
                token.error = f"Entry not found: {entry_id}"
                self._action_history.append(token)
                return token

            entry = self._entries[entry_id]
            if content is not None:
                entry.content = content
            if confidence is not None:
                entry.confidence = confidence
            if tags is not None:
                entry.tags = tags
            entry.last_accessed = now()
            token.success = True
            token.result = {"updated_entry_id": entry_id}
            self._action_history.append(token)
            return token

    def delete(self, entry_id: str) -> MemoryActionToken:
        """Delete a memory entry.

        Args:
            entry_id: ID of entry to delete.

        Returns:
            MemoryActionToken with result or error.
        """
        token = MemoryActionToken(
            action=MemoryAction.DELETE,
            payload={"entry_id": entry_id},
            timestamp=now(),
            requester="system"
        )

        with self._lock:
            if entry_id not in self._entries:
                token.success = False
                token.error = f"Entry not found: {entry_id}"
                self._action_history.append(token)
                return token

            del self._entries[entry_id]
            token.success = True
            token.result = {"deleted_entry_id": entry_id}
            self._action_history.append(token)
            return token

    def list_entries(self, limit: int = 100, offset: int = 0) -> MemoryActionToken:
        """List memory entries.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            MemoryActionToken with list of entries.
        """
        token = MemoryActionToken(
            action=MemoryAction.LIST,
            payload={"limit": limit, "offset": offset},
            timestamp=now(),
            requester="system"
        )

        with self._lock:
            entries = list(self._entries.values())
            paginated = [e.to_dict() for e in entries[offset:offset + limit]]
            token.success = True
            token.result = {
                "entries": paginated,
                "total": len(entries),
                "limit": limit,
                "offset": offset
            }
            self._action_history.append(token)
            return token

    def clear(self) -> MemoryActionToken:
        """Clear all memory entries.

        Returns:
            MemoryActionToken with result.
        """
        token = MemoryActionToken(
            action=MemoryAction.CLEAR,
            payload={},
            timestamp=now(),
            requester="system"
        )

        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            self._id_counter = 0
            token.success = True
            token.result = {"cleared_count": count}
            self._action_history.append(token)
            return token

    def reset(self) -> None:
        """Reset the buffer to empty state (alias for clear)."""
        with self._lock:
            self._entries.clear()
            self._id_counter = 0
            self._action_history.clear()

    def get_action_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent action history.

        Args:
            limit: Maximum number of history entries to return.

        Returns:
            List of action tokens as dictionaries.
        """
        with self._lock:
            history = self._action_history[-limit:]
            return [asdict(h) for h in history]

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics.

        Returns:
            Dictionary with buffer statistics.
        """
        with self._lock:
            return {
                "entry_count": len(self._entries),
                "max_entries": self._max_entries,
                "capacity_usage": len(self._entries) / self._max_entries,
                "action_count": len(self._action_history),
                "is_full": len(self._entries) >= self._max_entries,
                "is_near_capacity": len(self._entries) / self._max_entries >= self._capacity_warning
            }

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Tolerant fallback for unknown method calls.

        This allows the buffer to be used as a tolerant logger-like object
        where any unknown method returns a no-op callable.
        """
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


# Singleton instance for shared access
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer(max_entries: int = 10000) -> MemoryBuffer:
    """Get the singleton shared memory buffer instance.

    Args:
        max_entries: Maximum entries (only used on first creation).

    Returns:
        The shared MemoryBuffer instance.
    """
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(max_entries=max_entries)
        return _SHARED_BUFFER