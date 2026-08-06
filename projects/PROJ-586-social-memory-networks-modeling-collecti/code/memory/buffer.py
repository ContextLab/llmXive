"""Shared external memory buffer for multi-agent systems.

Implements a thread-safe memory buffer supporting <MEMORY_ACTION> tokens
with JSON schema: {"type": "write"|"read", "key": str, "value": str}
and queue-based write conflict resolution.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
MEMORY_ACTION_TOKEN_PATTERN = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"
MAX_QUEUE_SIZE = 1000

@dataclass
class MemoryAction:
    """Represents a memory operation (read or write)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.type not in ("write", "read"):
            raise ValueError(f"Invalid action type: {self.type}. Must be 'write' or 'read'.")
        if self.type == "write" and self.value is None:
            raise ValueError("Write actions must have a value.")
        if self.timestamp is None:
            self.timestamp = now()

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    agent_id: str
    timestamp: float
    version: int = 1

@dataclass
class WriteRequest:
    """A write request for conflict resolution."""
    action: MemoryAction
    request_id: str
    submitted_at: float = field(default_factory=now)

@dataclass
class ConflictResolutionResult:
    """Result of a conflict resolution attempt."""
    success: bool
    winning_request: Optional[WriteRequest] = None
    rejected_requests: List[WriteRequest] = field(default_factory=list)
    reason: str = ""

def now() -> float:
    """Return current timestamp."""
    return time.time()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token into a MemoryAction object."""
    match = re.search(MEMORY_ACTION_TOKEN_PATTERN, token, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(1))
        action_type = data.get("type")
        key = data.get("key")
        value = data.get("value")
        agent_id = data.get("agent_id")

        if not action_type or not key:
            return None

        return MemoryAction(
            type=action_type,
            key=key,
            value=value,
            agent_id=agent_id
        )
    except (json.JSONDecodeError, KeyError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token."""
    data = {
        "type": action.type,
        "key": action.key,
    }
    if action.value is not None:
        data["value"] = action.value
    if action.agent_id is not None:
        data["agent_id"] = action.agent_id

    return f"<MEMORY_ACTION>{json.dumps(data)}</MEMORY_ACTION>"

def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """Extract all memory actions from a prompt string."""
    actions = []
    pattern = re.compile(MEMORY_ACTION_TOKEN_PATTERN, re.DOTALL)
    matches = pattern.findall(prompt)

    for match in matches:
        try:
            data = json.loads(match)
            action_type = data.get("type")
            key = data.get("key")
            value = data.get("value")
            agent_id = data.get("agent_id")

            if action_type and key:
                actions.append(MemoryAction(
                    type=action_type,
                    key=key,
                    value=value,
                    agent_id=agent_id
                ))
        except (json.JSONDecodeError, KeyError):
            continue

    return actions

class WriteConflictResolver:
    """Resolves write conflicts using a queue-based approach."""

    def __init__(self, max_queue_size: int = MAX_QUEUE_SIZE):
        self._queue: deque = deque(maxlen=max_queue_size)
        self._lock = threading.Lock()
        self._request_counter = 0

    def submit(self, action: MemoryAction, agent_id: str) -> WriteRequest:
        """Submit a write request for conflict resolution."""
        self._request_counter += 1
        request = WriteRequest(
            action=action,
            request_id=f"{agent_id}_{self._request_counter}_{action.timestamp}"
        )

        with self._lock:
            self._queue.append(request)

        return request

    def resolve(self, key: str) -> ConflictResolutionResult:
        """Resolve conflicts for a given key using FIFO with timestamp tie-breaking."""
        with self._lock:
            # Filter requests for this key
            key_requests = [r for r in self._queue if r.action.key == key]

            if not key_requests:
                return ConflictResolutionResult(
                    success=False,
                    reason="No requests found for key"
                )

            if len(key_requests) == 1:
                # No conflict
                request = key_requests[0]
                self._queue.remove(request)
                return ConflictResolutionResult(
                    success=True,
                    winning_request=request
                )

            # Multiple requests - resolve by timestamp (oldest wins)
            key_requests.sort(key=lambda r: r.action.timestamp)
            winner = key_requests[0]
            losers = key_requests[1:]

            # Remove all from queue
            for req in key_requests:
                try:
                    self._queue.remove(req)
                except ValueError:
                    pass

            return ConflictResolutionResult(
                success=True,
                winning_request=winner,
                rejected_requests=losers,
                reason=f"Resolved {len(losers)} conflicting writes"
            )

    def reset(self):
        """Reset the resolver state."""
        with self._lock:
            self._queue.clear()
            self._request_counter = 0

    def get_pending_count(self) -> int:
        """Get the number of pending requests."""
        with self._lock:
            return len(self._queue)

class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems."""

    def __init__(self, max_size: int = 10000):
        self._buffer: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._write_queue: deque = deque(maxlen=MAX_QUEUE_SIZE)
        self._conflict_resolver = WriteConflictResolver()
        self._access_log: List[Dict[str, Any]] = []
        self._read_count = 0
        self._write_count = 0
        self._conflict_count = 0

    def write(self, key: str, value: str, agent_id: str) -> Tuple[bool, str]:
        """Write a value to the buffer with conflict resolution."""
        action = MemoryAction(
            type="write",
            key=key,
            value=value,
            agent_id=agent_id
        )

        # Submit for conflict resolution
        request = self._conflict_resolver.submit(action, agent_id)

        # Resolve conflicts
        result = self._conflict_resolver.resolve(key)

        if not result.success:
            return False, result.reason

        if result.winning_request != request:
            self._conflict_count += 1
            return False, f"Write conflict resolved: another request won for key '{key}'"

        with self._lock:
            # Check buffer size
            if len(self._buffer) >= self._max_size:
                # Evict oldest entry
                oldest_key = min(self._buffer.keys(), key=lambda k: self._buffer[k].timestamp)
                del self._buffer[oldest_key]

            # Get current version
            current_version = self._buffer.get(key, MemoryEntry(key, "", "", 0)).version + 1

            entry = MemoryEntry(
                key=key,
                value=value,
                agent_id=agent_id,
                timestamp=now(),
                version=current_version
            )

            self._buffer[key] = entry
            self._write_count += 1

            self._access_log.append({
                "action": "write",
                "key": key,
                "agent_id": agent_id,
                "timestamp": entry.timestamp,
                "version": current_version
            })

        return True, "Write successful"

    def read(self, key: str, agent_id: str) -> Tuple[Optional[str], Optional[int]]:
        """Read a value from the buffer."""
        with self._lock:
            entry = self._buffer.get(key)

            self._read_count += 1
            self._access_log.append({
                "action": "read",
                "key": key,
                "agent_id": agent_id,
                "timestamp": now(),
                "found": entry is not None
            })

            if entry is None:
                return None, None

            return entry.value, entry.version

    def delete(self, key: str, agent_id: str) -> bool:
        """Delete a key from the buffer."""
        with self._lock:
            if key in self._buffer:
                del self._buffer[key]
                self._access_log.append({
                    "action": "delete",
                    "key": key,
                    "agent_id": agent_id,
                    "timestamp": now()
                })
                return True
            return False

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get a full entry by key."""
        with self._lock:
            return self._buffer.get(key)

    def keys(self) -> List[str]:
        """Get all keys in the buffer."""
        with self._lock:
            return list(self._buffer.keys())

    def size(self) -> int:
        """Get the current buffer size."""
        with self._lock:
            return len(self._buffer)

    def reset(self):
        """Reset the buffer to empty state."""
        with self._lock:
            self._buffer.clear()
            self._write_queue.clear()
            self._access_log.clear()
            self._read_count = 0
            self._write_count = 0
            self._conflict_count = 0
        self._conflict_resolver.reset()

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        with self._lock:
            return {
                "size": len(self._buffer),
                "max_size": self._max_size,
                "total_reads": self._read_count,
                "total_writes": self._write_count,
                "conflicts": self._conflict_count,
                "pending_requests": self._conflict_resolver.get_pending_count()
            }

    def search(self, query: str) -> List[MemoryEntry]:
        """Search for entries containing the query string."""
        with self._lock:
            results = []
            query_lower = query.lower()
            for entry in self._buffer.values():
                if query_lower in entry.value.lower() or query_lower in entry.key.lower():
                    results.append(entry)
            return results

    # Tolerant fallback for any unknown method calls (logger-style)
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Shared buffer singleton
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

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token into a MemoryAction object."""
    match = re.search(MEMORY_ACTION_TOKEN_PATTERN, token, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(1))
        action_type = data.get("type")
        key = data.get("key")
        value = data.get("value")
        agent_id = data.get("agent_id")

        if not action_type or not key:
            return None

        return MemoryAction(
            type=action_type,
            key=key,
            value=value,
            agent_id=agent_id
        )
    except (json.JSONDecodeError, KeyError):
        return None