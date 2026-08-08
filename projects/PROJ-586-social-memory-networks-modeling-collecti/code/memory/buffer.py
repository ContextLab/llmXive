"""
Shared external memory buffer for multi-agent social memory networks.
Implements queue-based write conflict resolution and <MEMORY_ACTION> token handling.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class MemoryAction:
    """Represents a single memory operation."""
    type: str  # 'write' or 'read'
    key: str
    value: Optional[str] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    agent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryAction:
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value"),
            timestamp=data.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            agent_id=data.get("agent_id")
        )

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    agent_id: str
    timestamp: str
    version: int = 1
    access_count: int = 0
    last_accessed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed
        }

@dataclass
class WriteRequest:
    """A request to write to the memory buffer."""
    key: str
    value: str
    agent_id: str
    timestamp: str

@dataclass
class ConflictResolutionResult:
    """Result of a write conflict resolution."""
    success: bool
    winning_key: str
    winning_agent: str
    rejected_agent: Optional[str] = None
    resolution_method: str = "queue_order"  # or "priority", "timestamp", etc.

class WriteConflictResolver:
    """
    Handles write conflicts using a queue-based approach.
    When multiple agents try to write to the same key, the first in queue wins.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._write_queues: Dict[str, deque] = {}  # key -> deque of WriteRequest
        self._pending_resolutions: Dict[str, List[ConflictResolutionResult]] = {}

    def submit_write_request(self, request: WriteRequest) -> ConflictResolutionResult:
        """
        Submit a write request. If the key is already being written to,
        queue the request and resolve conflicts.
        """
        with self._lock:
            key = request.key

            if key not in self._write_queues:
                # First request for this key - grant immediately
                self._write_queues[key] = deque([request])
                return ConflictResolutionResult(
                    success=True,
                    winning_key=key,
                    winning_agent=request.agent_id,
                    resolution_method="queue_order"
                )

            # Key is already in queue - add to end
            self._write_queues[key].append(request)

            # Resolve: first in queue wins
            winning_request = self._write_queues[key][0]
            result = ConflictResolutionResult(
                success=(request.agent_id == winning_request.agent_id),
                winning_key=key,
                winning_agent=winning_request.agent_id,
                rejected_agent=request.agent_id if request.agent_id != winning_request.agent_id else None,
                resolution_method="queue_order"
            )

            return result

    def release_key(self, key: str, agent_id: str) -> bool:
        """
        Release a key after write is complete. Removes the request from the queue.
        If there are pending requests, the next one becomes active.
        """
        with self._lock:
            if key not in self._write_queues:
                return False

            queue = self._write_queues[key]
            if not queue:
                del self._write_queues[key]
                return True

            # Remove the completed request
            if queue[0].agent_id == agent_id:
                queue.popleft()
                if not queue:
                    del self._write_queues[key]
                return True

            return False

    def reset(self) -> None:
        """Reset the conflict resolver state."""
        with self._lock:
            self._write_queues.clear()
            self._pending_resolutions.clear()

class MemoryBuffer:
    """
    Shared external memory buffer for multi-agent systems.
    Supports <MEMORY_ACTION> tokens with JSON schema:
    {"type": "write"|"read", "key": str, "value": str}
    """

    def __init__(self, max_size: int = 10000):
        self._lock = threading.RLock()
        self._memory: Dict[str, MemoryEntry] = {}
        self._access_log: deque = deque(maxlen=10000)
        self._max_size = max_size
        self._conflict_resolver = WriteConflictResolver()
        self._write_in_progress: Dict[str, str] = {}  # key -> agent_id

    def write(self, key: str, value: str, agent_id: str) -> ConflictResolutionResult:
        """
        Write a value to memory. Handles conflicts via queue-based resolution.
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        request = WriteRequest(key=key, value=value, agent_id=agent_id, timestamp=timestamp)

        # Check for conflict
        result = self._conflict_resolver.submit_write_request(request)

        if not result.success:
            logger.debug(f"Write conflict for key '{key}': {result.resolution_method}")
            return result

        # Acquire write lock
        with self._lock:
            # Check if we're still the winner (queue might have changed)
            if key in self._write_in_progress and self._write_in_progress[key] != agent_id:
                return ConflictResolutionResult(
                    success=False,
                    winning_key=key,
                    winning_agent=self._write_in_progress[key],
                    rejected_agent=agent_id,
                    resolution_method="queue_order"
                )

            # Perform the write
            if key in self._memory:
                entry = self._memory[key]
                new_entry = MemoryEntry(
                    key=key,
                    value=value,
                    agent_id=agent_id,
                    timestamp=timestamp,
                    version=entry.version + 1,
                    access_count=entry.access_count,
                    last_accessed=entry.last_accessed
                )
            else:
                # Check size limit
                if len(self._memory) >= self._max_size:
                    # Simple eviction: remove oldest entry
                    oldest_key = min(self._memory.keys(), key=lambda k: self._memory[k].timestamp)
                    del self._memory[oldest_key]

                new_entry = MemoryEntry(
                    key=key,
                    value=value,
                    agent_id=agent_id,
                    timestamp=timestamp,
                    version=1,
                    access_count=0,
                    last_accessed=None
                )

            self._memory[key] = new_entry
            self._write_in_progress[key] = agent_id

            # Log the write
            self._access_log.append({
                "action": "write",
                "key": key,
                "agent_id": agent_id,
                "timestamp": timestamp
            })

            # Release the key
            self._conflict_resolver.release_key(key, agent_id)
            if key in self._write_in_progress and self._write_in_progress[key] == agent_id:
                del self._write_in_progress[key]

            return result

    def read(self, key: str, agent_id: str) -> Optional[MemoryEntry]:
        """
        Read a value from memory. Updates access statistics.
        """
        with self._lock:
            if key not in self._memory:
                return None

            entry = self._memory[key]
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            # Update access statistics
            updated_entry = MemoryEntry(
                key=entry.key,
                value=entry.value,
                agent_id=entry.agent_id,
                timestamp=entry.timestamp,
                version=entry.version,
                access_count=entry.access_count + 1,
                last_accessed=timestamp
            )
            self._memory[key] = updated_entry

            # Log the read
            self._access_log.append({
                "action": "read",
                "key": key,
                "agent_id": agent_id,
                "timestamp": timestamp
            })

            return updated_entry

    def parse_memory_action_token(self, token: str) -> Optional[MemoryAction]:
        """
        Parse a <MEMORY_ACTION> token into a MemoryAction object.
        Token format: <MEMORY_ACTION>{"type": "write", "key": "...", "value": "..."}</MEMORY_ACTION>
        """
        pattern = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"
        match = re.search(pattern, token, re.DOTALL)

        if not match:
            return None

        try:
            action_data = json.loads(match.group(1))
            return MemoryAction.from_dict(action_data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse MEMORY_ACTION token: {e}")
            return None

    def format_action_token(self, action: MemoryAction) -> str:
        """
        Format a MemoryAction as a <MEMORY_ACTION> token.
        """
        action_json = json.dumps(action.to_dict())
        return f"<MEMORY_ACTION>{action_json}</MEMORY_ACTION>"

    def parse_action_from_prompt(self, prompt: str) -> List[MemoryAction]:
        """
        Extract all <MEMORY_ACTION> tokens from a prompt string.
        """
        actions = []
        pattern = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"

        for match in re.finditer(pattern, prompt, re.DOTALL):
            try:
                action_data = json.loads(match.group(1))
                actions.append(MemoryAction.from_dict(action_data))
            except (json.JSONDecodeError, KeyError):
                continue

        return actions

    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """Get a raw entry without updating access stats."""
        with self._lock:
            return self._memory.get(key)

    def get_all_keys(self) -> List[str]:
        """Get all keys in the memory buffer."""
        with self._lock:
            return list(self._memory.keys())

    def get_memory_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Get a snapshot of the entire memory buffer."""
        with self._lock:
            return {key: entry.to_dict() for key, entry in self._memory.items()}

    def get_access_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the most recent access log entries."""
        with self._lock:
            return list(self._access_log)[-limit:]

    def size(self) -> int:
        """Get the current number of entries in the buffer."""
        with self._lock:
            return len(self._memory)

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._memory.clear()
            self._access_log.clear()

    def reset(self) -> None:
        """Reset the buffer to initial state."""
        with self._lock:
            self._memory.clear()
            self._access_log.clear()
            self._write_in_progress.clear()
            self._conflict_resolver.reset()

    # Tolerant attribute access for logger-like calls
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Singleton shared buffer instance
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(max_size: int = 10000) -> MemoryBuffer:
    """Get the singleton shared memory buffer instance."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(max_size=max_size)
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the singleton shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
            _SHARED_BUFFER = None

# Utility functions for token parsing/formatting
def now() -> str:
    """Get current timestamp in ISO format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token."""
    buffer = get_shared_buffer()
    return buffer.parse_memory_action_token(token)

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a token."""
    buffer = get_shared_buffer()
    return buffer.format_action_token(action)

def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """Extract actions from a prompt."""
    buffer = get_shared_buffer()
    return buffer.parse_action_from_prompt(prompt)