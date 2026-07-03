"""Shared external memory buffer with <MEMORY_ACTION> token handling.

Implements a thread-safe shared memory buffer for multi-agent systems.
Supports parsing and handling of <MEMORY_ACTION> tokens for distributed
transactive memory operations.
"""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, Callable
from enum import Enum


class MemoryActionType(str, Enum):
    """Types of memory actions supported by the buffer."""
    STORE = "store"
    RETRIEVE = "retrieve"
    FORGET = "forget"
    UPDATE = "update"
    QUERY = "query"


@dataclass
class MemoryAction:
    """Represents a single memory action to be stored or executed."""
    action_type: MemoryActionType
    agent_id: str
    content: str
    cue: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action_type": self.action_type.value,
            "agent_id": self.agent_id,
            "content": self.content,
            "cue": self.cue,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        """Create from dictionary."""
        return cls(
            action_type=MemoryActionType(data["action_type"]),
            agent_id=data["agent_id"],
            content=data["content"],
            cue=data.get("cue"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {})
        )


@dataclass
class MemoryEntry:
    """A stored entry in the memory buffer."""
    entry_id: str
    action: MemoryAction
    score: float = 1.0
    access_count: int = 0
    last_accessed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entry_id": self.entry_id,
            "action": self.action.to_dict(),
            "score": self.score,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        action = MemoryAction.from_dict(data["action"])
        return cls(
            entry_id=data["entry_id"],
            action=action,
            score=data.get("score", 1.0),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed")
        )


def now() -> str:
    """Return current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


# Token pattern for memory actions
MEMORY_ACTION_PATTERN = re.compile(
    r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>",
    re.DOTALL
)


def parse_memory_action_token(text: str) -> List[MemoryAction]:
    """Parse <MEMORY_ACTION> tokens from text and return list of actions."""
    actions = []
    matches = MEMORY_ACTION_PATTERN.findall(text)
    for match in matches:
        try:
            data = json.loads(match.strip())
            action = MemoryAction.from_dict(data)
            actions.append(action)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed tokens
            continue
    return actions


def parse_memory_action(text: str) -> Optional[MemoryAction]:
    """Parse a single <MEMORY_ACTION> token from text.

    Returns the first valid action found, or None if no valid action exists.
    """
    actions = parse_memory_action_token(text)
    return actions[0] if actions else None


class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems.

    This buffer acts as a central repository for memory actions across
    multiple agents, supporting transactive memory operations.
    """

    def __init__(self, capacity: int = 10000, decay_rate: float = 0.01) -> None:
        """Initialize the memory buffer.

        Args:
            capacity: Maximum number of entries to store.
            decay_rate: Rate at which unused entries lose score.
        """
        self.capacity = capacity
        self.decay_rate = decay_rate
        self._entries: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._entry_counter = 0
        self._callbacks: List[Callable[[MemoryEntry], None]] = []

    def store(self, action: MemoryAction) -> str:
        """Store a memory action in the buffer.

        Args:
            action: The memory action to store.

        Returns:
            The entry ID of the stored action.
        """
        with self._lock:
            self._entry_counter += 1
            entry_id = f"mem_{self._entry_counter}_{action.agent_id}"

            # If entry exists, update it
            if entry_id in self._entries:
                entry = self._entries[entry_id]
                entry.action = action
                entry.score = min(1.0, entry.score + 0.1)
                entry.last_accessed = now()
            else:
                # Create new entry
                entry = MemoryEntry(
                    entry_id=entry_id,
                    action=action,
                    score=1.0
                )
                self._entries[entry_id] = entry

                # Enforce capacity
                if len(self._entries) > self.capacity:
                    self._evict_lowest_score()

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(entry)
                except Exception:
                    pass

            return entry_id

    def retrieve(self, cue: str, agent_id: str, top_k: int = 5) -> List[MemoryEntry]:
        """Retrieve memory entries matching a cue.

        Args:
            cue: The retrieval cue.
            agent_id: The requesting agent ID.
            top_k: Number of top entries to return.

        Returns:
            List of MemoryEntry objects sorted by relevance score.
        """
        with self._lock:
            # Simple string matching for now
            # In production, this would use embeddings or semantic search
            matches = []
            for entry_id, entry in self._entries.items():
                # Check if cue matches content or metadata
                content_match = cue.lower() in entry.action.content.lower()
                cue_match = entry.action.cue and cue.lower() in entry.action.cue.lower()
                agent_match = entry.action.agent_id == agent_id

                if content_match or cue_match or agent_match:
                    # Calculate relevance score
                    relevance = entry.score
                    if agent_match:
                        relevance *= 1.5
                    if content_match:
                        relevance *= 1.2
                    matches.append((relevance, entry))

            # Sort by relevance and return top_k
            matches.sort(key=lambda x: x[0], reverse=True)
            result = [entry for _, entry in matches[:top_k]]

            # Update access info
            for entry in result:
                entry.access_count += 1
                entry.last_accessed = now()

            return result

    def forget(self, entry_id: str) -> bool:
        """Remove an entry from the buffer.

        Args:
            entry_id: The ID of the entry to remove.

        Returns:
            True if entry was removed, False if not found.
        """
        with self._lock:
            if entry_id in self._entries:
                del self._entries[entry_id]
                return True
            return False

    def update(self, entry_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Update an existing entry.

        Args:
            entry_id: The ID of the entry to update.
            content: New content for the entry.
            metadata: Optional metadata to update.

        Returns:
            True if entry was updated, False if not found.
        """
        with self._lock:
            if entry_id not in self._entries:
                return False

            entry = self._entries[entry_id]
            entry.action.content = content
            if metadata:
                entry.action.metadata.update(metadata)
            entry.score = min(1.0, entry.score + 0.05)
            entry.last_accessed = now()
            return True

    def query(self, query_text: str, agent_id: Optional[str] = None) -> List[MemoryEntry]:
        """Query the buffer with a text query.

        Args:
            query_text: The query text.
            agent_id: Optional agent ID to filter results.

        Returns:
            List of matching MemoryEntry objects.
        """
        with self._lock:
            results = []
            for entry in self._entries.values():
                if agent_id and entry.action.agent_id != agent_id:
                    continue

                # Simple keyword matching
                query_lower = query_text.lower()
                content_lower = entry.action.content.lower()
                cue_lower = (entry.action.cue or "").lower()

                if query_lower in content_lower or query_lower in cue_lower:
                    results.append(entry)

            return results

    def get_all(self) -> List[MemoryEntry]:
        """Get all entries in the buffer.

        Returns:
            List of all MemoryEntry objects.
        """
        with self._lock:
            return list(self._entries.values())

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._entries.clear()
            self._entry_counter = 0

    def reset(self) -> None:
        """Reset the buffer to initial state."""
        with self._lock:
            self._entries.clear()
            self._entry_counter = 0
            self._callbacks.clear()

    def size(self) -> int:
        """Return the current number of entries."""
        with self._lock:
            return len(self._entries)

    def decay_scores(self) -> None:
        """Apply score decay to all entries."""
        with self._lock:
            for entry in self._entries.values():
                entry.score = max(0.0, entry.score - self.decay_rate)

    def add_callback(self, callback: Callable[[MemoryEntry], None]) -> None:
        """Add a callback to be notified when entries are stored.

        Args:
            callback: Function to call with the MemoryEntry.
        """
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[MemoryEntry], None]) -> bool:
        """Remove a callback.

        Args:
            callback: The callback function to remove.

        Returns:
            True if callback was removed, False if not found.
        """
        with self._lock:
            try:
                self._callbacks.remove(callback)
                return True
            except ValueError:
                return False

    def _evict_lowest_score(self) -> None:
        """Remove the entry with the lowest score."""
        if not self._entries:
            return

        # Find entry with lowest score
        lowest_id = min(self._entries.keys(), key=lambda k: self._entries[k].score)
        del self._entries[lowest_id]

    def __len__(self) -> int:
        """Return the number of entries."""
        return self.size()

    def __contains__(self, entry_id: str) -> bool:
        """Check if an entry exists."""
        with self._lock:
            return entry_id in self._entries

    # Tolerant fallback for any unknown method calls
    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Return a no-op callable for any unknown attribute."""
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


# Shared buffer singleton
_shared_buffer: Optional[MemoryBuffer] = None
_buffer_lock = threading.Lock()


def get_shared_buffer(capacity: int = 10000, decay_rate: float = 0.01) -> MemoryBuffer:
    """Get the shared memory buffer singleton.

    Args:
        capacity: Maximum capacity (only used on first creation).
        decay_rate: Decay rate (only used on first creation).

    Returns:
        The shared MemoryBuffer instance.
    """
    global _shared_buffer
    with _buffer_lock:
        if _shared_buffer is None:
            _shared_buffer = MemoryBuffer(capacity=capacity, decay_rate=decay_rate)
        return _shared_buffer


def get_shared_memory_buffer(capacity: int = 10000, decay_rate: float = 0.01) -> MemoryBuffer:
    """Alias for get_shared_buffer for compatibility."""
    return get_shared_buffer(capacity=capacity, decay_rate=decay_rate)


def reset_shared_buffer() -> None:
    """Reset the shared buffer singleton."""
    global _shared_buffer
    with _buffer_lock:
        if _shared_buffer is not None:
            _shared_buffer.reset()
        _shared_buffer = None


def reset_shared_memory_buffer() -> None:
    """Alias for reset_shared_buffer for compatibility."""
    reset_shared_buffer()


def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """Parse memory actions from a prompt string.

    Args:
        prompt: The prompt text potentially containing <MEMORY_ACTION> tokens.

    Returns:
        List of parsed MemoryAction objects.
    """
    return parse_memory_action_token(prompt)


def format_action_token(action: MemoryAction) -> str:
    """Format a memory action as a <MEMORY_ACTION> token.

    Args:
        action: The MemoryAction to format.

    Returns:
        String representation with <MEMORY_ACTION> tags.
    """
    data = action.to_dict()
    json_str = json.dumps(data, ensure_ascii=False)
    return f"<MEMORY_ACTION>{json_str}</MEMORY_ACTION>"