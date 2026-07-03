"""Shared external memory buffer with <MEMORY_ACTION> token handling.

This module implements a thread-safe singleton memory buffer that agents can
use to store, retrieve, and delete shared memory entries. It also provides
utilities for parsing and formatting <MEMORY_ACTION> tokens that represent
memory operations in agent communication.
"""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from pathlib import Path


class MemoryActionType(Enum):
    """Types of memory actions that can be performed."""
    WRITE = "write"
    READ = "read"
    DELETE = "delete"
    SEARCH = "search"
    UPDATE = "update"


@dataclass
class MemoryAction:
    """Represents a single memory action."""
    action_type: MemoryActionType
    key: Optional[str] = None
    value: Optional[str] = None
    query: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "action_type": self.action_type.value,
            "key": self.key,
            "value": self.value,
            "query": self.query,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        """Create from dictionary representation."""
        return cls(
            action_type=MemoryActionType(data["action_type"]),
            key=data.get("key"),
            value=data.get("value"),
            query=data.get("query"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )


@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary representation."""
        return cls(**data)


# Token pattern for <MEMORY_ACTION> tokens
MEMORY_ACTION_PATTERN = re.compile(
    r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>",
    re.DOTALL
)


def now() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token string into a MemoryAction object.

    Args:
        token: The token string to parse, e.g., "<MEMORY_ACTION>write:key=value</MEMORY_ACTION>"

    Returns:
        MemoryAction object if parsing succeeds, None otherwise.
    """
    match = MEMORY_ACTION_PATTERN.search(token)
    if not match:
        return None

    content = match.group(1).strip()
    try:
        # Try JSON first
        data = json.loads(content)
        return MemoryAction.from_dict(data)
    except json.JSONDecodeError:
        pass

    # Try simple key=value format
    parts = content.split(":", 1)
    if len(parts) >= 2:
        action_type_str = parts[0].strip().lower()
        try:
            action_type = MemoryActionType(action_type_str)
        except ValueError:
            return None

        remaining = parts[1].strip()
        if "=" in remaining:
            key, value = remaining.split("=", 1)
            return MemoryAction(
                action_type=action_type,
                key=key.strip(),
                value=value.strip()
            )
        else:
            return MemoryAction(
                action_type=action_type,
                query=remaining
            )

    return None


def parse_memory_action(text: str) -> List[MemoryAction]:
    """Parse all <MEMORY_ACTION> tokens from a text string.

    Args:
        text: The text to search for tokens.

    Returns:
        List of MemoryAction objects found in the text.
    """
    actions = []
    for match in MEMORY_ACTION_PATTERN.finditer(text):
        action = parse_memory_action_token(match.group(0))
        if action:
            actions.append(action)
    return actions


def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction object as a <MEMORY_ACTION> token.

    Args:
        action: The MemoryAction to format.

    Returns:
        String representation of the token.
    """
    return f"<MEMORY_ACTION>{json.dumps(action.to_dict())}</MEMORY_ACTION>"


def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """Parse memory actions from a natural language prompt.

    This is a simple parser that looks for <MEMORY_ACTION> tokens in the prompt.
    For more sophisticated parsing, an LLM would be used to extract actions.

    Args:
        prompt: The prompt text to parse.

    Returns:
        List of MemoryAction objects found in the prompt.
    """
    return parse_memory_action(prompt)


class MemoryBuffer:
    """Thread-safe singleton memory buffer for shared agent memory.

    This buffer provides a shared space where multiple agents can store,
    retrieve, update, and delete memory entries. It supports concurrent
    access through locking.
    """

    _instance: Optional["MemoryBuffer"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the memory buffer."""
        # Prevent re-initialization
        if hasattr(self, '_initialized'):
            return

        self._entries: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._max_entries: int = 10000  # Default max entries
        self._initialized = True

    def reset(self) -> None:
        """Reset the buffer to empty state."""
        with self._lock:
            self._entries.clear()

    def set_max_entries(self, max_entries: int) -> None:
        """Set the maximum number of entries allowed in the buffer."""
        with self._lock:
            self._max_entries = max_entries

    def write(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Write a new entry to the buffer.

        Args:
            key: Unique key for the entry.
            value: The value to store.
            metadata: Optional metadata dictionary.

        Returns:
            True if write was successful, False otherwise.
        """
        with self._lock:
            # Check max entries
            if key not in self._entries and len(self._entries) >= self._max_entries:
                return False

            entry = MemoryEntry(
                key=key,
                value=value,
                metadata=metadata or {},
                created_at=now(),
                updated_at=now()
            )
            self._entries[key] = entry
            return True

    def read(self, key: str) -> Optional[MemoryEntry]:
        """Read an entry from the buffer.

        Args:
            key: The key of the entry to read.

        Returns:
            MemoryEntry if found, None otherwise.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry:
                entry.access_count += 1
                return entry
            return None

    def delete(self, key: str) -> bool:
        """Delete an entry from the buffer.

        Args:
            key: The key of the entry to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False

    def update(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing entry in the buffer.

        Args:
            key: The key of the entry to update.
            value: The new value.
            metadata: Optional new metadata.

        Returns:
            True if update was successful, False otherwise.
        """
        with self._lock:
            if key not in self._entries:
                return False

            entry = self._entries[key]
            entry.value = value
            entry.updated_at = now()
            if metadata:
                entry.metadata.update(metadata)
            return True

    def search(self, query: str) -> List[MemoryEntry]:
        """Search for entries matching the query.

        Args:
            query: Search query string.

        Returns:
            List of matching MemoryEntry objects.
        """
        with self._lock:
            results = []
            query_lower = query.lower()
            for entry in self._entries.values():
                if query_lower in entry.value.lower() or query_lower in entry.key.lower():
                    entry.access_count += 1
                    results.append(entry)
            return results

    def get_all(self) -> List[MemoryEntry]:
        """Get all entries in the buffer.

        Returns:
            List of all MemoryEntry objects.
        """
        with self._lock:
            return list(self._entries.values())

    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """Get a specific entry by key.

        Args:
            key: The key of the entry.

        Returns:
            MemoryEntry if found, None otherwise.
        """
        return self.read(key)

    def contains(self, key: str) -> bool:
        """Check if a key exists in the buffer.

        Args:
            key: The key to check.

        Returns:
            True if key exists, False otherwise.
        """
        with self._lock:
            return key in self._entries

    def size(self) -> int:
        """Get the current number of entries in the buffer.

        Returns:
            Number of entries.
        """
        with self._lock:
            return len(self._entries)

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._entries.clear()

    def export_to_file(self, filepath: Union[str, Path]) -> None:
        """Export all entries to a JSON file.

        Args:
            filepath: Path to the output file.
        """
        with self._lock:
            data = {
                "entries": [entry.to_dict() for entry in self._entries.values()],
                "exported_at": now()
            }
            Path(filepath).write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def import_from_file(self, filepath: Union[str, Path]) -> int:
        """Import entries from a JSON file.

        Args:
            filepath: Path to the input file.

        Returns:
            Number of entries imported.
        """
        with self._lock:
            data = json.loads(Path(filepath).read_text())
            count = 0
            for entry_data in data.get("entries", []):
                entry = MemoryEntry.from_dict(entry_data)
                self._entries[entry.key] = entry
                count += 1
            return count

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Provide tolerant fallback for unknown method calls.

        This allows the buffer to be used like a logger where any
        unrecognized method call becomes a no-op instead of raising
        an AttributeError.
        """
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


# Global singleton instance
_SHARED_BUFFER: Optional[MemoryBuffer] = None


def get_shared_buffer() -> MemoryBuffer:
    """Get the singleton shared memory buffer instance.

    Returns:
        The singleton MemoryBuffer instance.
    """
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER


def reset_shared_buffer() -> None:
    """Reset the shared memory buffer to empty state."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is not None:
        _SHARED_BUFFER.reset()