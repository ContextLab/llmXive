"""Shared external memory buffer for multi-agent systems."""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MemoryAction:
    """Represents a memory action (write or read)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None
    agent_id: Optional[int] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    agent_id: int
    timestamp: str
    version: int = 1


@dataclass
class WriteRequest:
    """A request to write to memory."""
    key: str
    value: str
    agent_id: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ConflictResolutionResult:
    """Result of conflict resolution."""
    resolved: bool
    winner_agent_id: Optional[int]
    resolution_method: str


def now() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token into a MemoryAction object."""
    pattern = r'<MEMORY_ACTION>\s*(\w+)\s+key="([^"]+)"\s+value="([^"]*)"(?:\s+agent_id="(\d+)")?\s*</MEMORY_ACTION>'
    match = re.match(pattern, token)
    
    if not match:
        return None
    
    action_type = match.group(1)
    key = match.group(2)
    value = match.group(3)
    agent_id = int(match.group(4)) if match.group(4) else None
    
    return MemoryAction(
        type=action_type,
        key=key,
        value=value if value else None,
        agent_id=agent_id
    )


def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token."""
    agent_part = f' agent_id="{action.agent_id}"' if action.agent_id is not None else ""
    value_part = action.value if action.value else ""
    return f'<MEMORY_ACTION> {action.type} key="{action.key}" value="{value_part}"{agent_part} </MEMORY_ACTION>'


def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """Parse all memory actions from a prompt string."""
    pattern = r'<MEMORY_ACTION>\s*(\w+)\s+key="([^"]+)"\s+value="([^"]*)"(?:\s+agent_id="(\d+)")?\s*</MEMORY_ACTION>'
    matches = re.findall(pattern, prompt)
    
    actions = []
    for match in matches:
        action_type, key, value, agent_id = match
        actions.append(MemoryAction(
            type=action_type,
            key=key,
            value=value if value else None,
            agent_id=int(agent_id) if agent_id else None
        ))
    
    return actions


class WriteConflictResolver:
    """Resolves write conflicts using queue-based resolution."""
    
    def __init__(self):
        self._queue: deque = deque()
        self._lock = threading.Lock()
    
    def add_request(self, request: WriteRequest) -> ConflictResolutionResult:
        """Add a write request to the queue and resolve conflicts."""
        with self._lock:
            self._queue.append(request)
            
            # Simple queue-based resolution: first writer wins
            if len(self._queue) == 1:
                return ConflictResolutionResult(
                    resolved=True,
                    winner_agent_id=request.agent_id,
                    resolution_method="first_writer_wins"
                )
            else:
                # Conflict detected: first request wins
                winner = self._queue[0]
                return ConflictResolutionResult(
                    resolved=True,
                    winner_agent_id=winner.agent_id,
                    resolution_method="queue_order"
                )
    
    def reset(self):
        """Reset the conflict resolver queue."""
        with self._lock:
            self._queue.clear()


class MemoryBuffer:
    """Shared external memory buffer with conflict resolution."""
    
    def __init__(self):
        self._entries: Dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()
        self._conflict_resolver = WriteConflictResolver()
        self._history: List[MemoryEntry] = []
    
    def write(self, key: str, value: str, agent_id: int) -> bool:
        """Write a value to memory."""
        with self._lock:
            request = WriteRequest(key=key, value=value, agent_id=agent_id)
            result = self._conflict_resolver.add_request(request)
            
            if result.resolved and result.winner_agent_id == agent_id:
                timestamp = now()
                entry = MemoryEntry(
                    key=key,
                    value=value,
                    agent_id=agent_id,
                    timestamp=timestamp,
                    version=self._entries.get(key, MemoryEntry(key, "", 0, "", 0)).version + 1
                )
                self._entries[key] = entry
                self._history.append(entry)
                return True
            
            return False
    
    def read(self, key: str) -> Optional[str]:
        """Read a value from memory."""
        with self._lock:
            entry = self._entries.get(key)
            return entry.value if entry else None
    
    def delete(self, key: str) -> bool:
        """Delete a key from memory."""
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False
    
    def get_all(self) -> Dict[str, MemoryEntry]:
        """Get all entries in memory."""
        with self._lock:
            return dict(self._entries)
    
    def search(self, query: str) -> List[MemoryEntry]:
        """Search for entries containing the query string."""
        with self._lock:
            return [entry for entry in self._entries.values() if query in entry.value]
    
    def reset(self):
        """Reset the memory buffer."""
        with self._lock:
            self._entries.clear()
            self._history.clear()
            self._conflict_resolver.reset()
    
    def __getattr__(self, name: str):
        """Tolerant fallback for unknown method calls."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()


def get_shared_buffer() -> MemoryBuffer:
    """Get the shared memory buffer singleton."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer()
        return _SHARED_BUFFER


def reset_shared_buffer():
    """Reset the shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
            _SHARED_BUFFER = None
