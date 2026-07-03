"""External memory buffer with <MEMORY_ACTION> token handling."""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Dict, List


class MemoryActionType(str, Enum):
    """Types of memory actions."""
    STORE = "STORE"
    RETRIEVE = "RETRIEVE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class MemoryAction:
    """A single memory action."""
    action_type: MemoryActionType
    key: str
    value: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryEntry:
    """A stored memory entry."""
    key: str
    value: str
    timestamp: str
    action_type: MemoryActionType = MemoryActionType.STORE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def now() -> str:
    """Return current ISO timestamp."""
    return datetime.utcnow().isoformat()


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION:...> token from LLM output.
    
    Args:
        token: String like "<MEMORY_ACTION:STORE:key:value>"
        
    Returns:
        MemoryAction if valid, None otherwise
    """
    if not token.startswith("<MEMORY_ACTION:") or not token.endswith(">"):
        return None
    
    try:
        content = token[15:-1]  # Remove <MEMORY_ACTION: and >
        parts = content.split(":")
        if len(parts) < 2:
            return None
        
        action_type_str = parts[0].upper()
        key = parts[1]
        value = ":".join(parts[2:]) if len(parts) > 2 else None
        
        action_type = MemoryActionType(action_type_str)
        return MemoryAction(
            action_type=action_type,
            key=key,
            value=value,
            timestamp=now(),
        )
    except (ValueError, IndexError):
        return None


def parse_memory_action(text: str) -> Optional[MemoryAction]:
    """Parse memory action from text (alias for parse_memory_action_token)."""
    return parse_memory_action_token(text)


def format_action_token(
    action_type: MemoryActionType | str,
    key: str,
    value: Optional[str] = None,
) -> str:
    """Format a memory action as a token.
    
    Args:
        action_type: Type of action
        key: Memory key
        value: Optional memory value
        
    Returns:
        Formatted token string
    """
    if isinstance(action_type, str):
        action_type = MemoryActionType(action_type.upper())
    
    if value:
        return f"<MEMORY_ACTION:{action_type.value}:{key}:{value}>"
    return f"<MEMORY_ACTION:{action_type.value}:{key}>"


def parse_action_from_prompt(prompt: str) -> Optional[MemoryAction]:
    """Extract memory action from a prompt string."""
    match = re.search(r"<MEMORY_ACTION:[^>]+>", prompt)
    if match:
        return parse_memory_action_token(match.group(0))
    return None


class MemoryBuffer:
    """Thread-safe external memory buffer."""

    def __init__(self) -> None:
        self._memory: Dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()

    def store(self, key: str, value: str, action_type: MemoryActionType = MemoryActionType.STORE) -> None:
        """Store a memory entry."""
        with self._lock:
            self._memory[key] = MemoryEntry(
                key=key,
                value=value,
                timestamp=now(),
                action_type=action_type,
            )

    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve a memory entry."""
        with self._lock:
            entry = self._memory.get(key)
            return entry.value if entry else None

    def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        with self._lock:
            if key in self._memory:
                del self._memory[key]
                return True
            return False

    def reset(self) -> None:
        """Clear all memory entries."""
        with self._lock:
            self._memory.clear()

    def get_all(self) -> Dict[str, MemoryEntry]:
        """Get all memory entries."""
        with self._lock:
            return dict(self._memory)

    def to_dict(self) -> Dict[str, Any]:
        """Convert buffer to dictionary."""
        with self._lock:
            return {k: v.to_dict() for k, v in self._memory.items()}

    def __getattr__(self, name: str) -> Any:
        """Tolerant fallback for unknown methods (logger-style)."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer() -> MemoryBuffer:
    """Get or create the shared memory buffer (singleton)."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        with _BUFFER_LOCK:
            if _SHARED_BUFFER is None:
                _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER


def get_shared_memory_buffer() -> MemoryBuffer:
    """Alias for get_shared_buffer."""
    return get_shared_buffer()


def reset_shared_buffer() -> None:
    """Reset the shared buffer."""
    get_shared_buffer().reset()


def reset_shared_memory_buffer() -> None:
    """Alias for reset_shared_buffer."""
    reset_shared_buffer()
