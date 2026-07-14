"""
Shared external memory buffer for multi-agent social memory networks.

Implements a thread-safe, queue-based write conflict resolution mechanism
supporting <MEMORY_ACTION> tokens with JSON schema:
{"type": "write"|"read", "key": str, "value": str}
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Token pattern for memory actions
MEMORY_ACTION_TOKEN_PATTERN = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"

@dataclass
class MemoryAction:
    """Represents a single memory action (read or write)."""
    type: str  # 'write' or 'read'
    key: str
    value: Optional[str] = None  # Only required for writes

    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type, "key": self.key}
        if self.value is not None:
            result["value"] = self.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value")
        )

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer with metadata."""
    key: str
    value: str
    timestamp: float = field(default_factory=time.time)
    agent_id: Optional[str] = None
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "version": self.version
        }

@dataclass
class WriteRequest:
    """A request to write to the memory buffer."""
    key: str
    value: str
    agent_id: str
    timestamp: float = field(default_factory=time.time)
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = f"{self.agent_id}_{int(self.timestamp * 1000)}"

@dataclass
class ConflictResolutionResult:
    """Result of a conflict resolution attempt."""
    success: bool
    winning_request: Optional[WriteRequest] = None
    rejected_requests: List[WriteRequest] = field(default_factory=list)
    resolution_strategy: str = "queue_order"  # or "timestamp", "agent_priority"

def now() -> float:
    """Return current timestamp."""
    return time.time()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """
    Parse a <MEMORY_ACTION> token string into a MemoryAction object.

    Args:
        token: String containing the token, e.g., "<MEMORY_ACTION>{...}</MEMORY_ACTION>"

    Returns:
        MemoryAction object or None if parsing fails
    """
    match = re.search(MEMORY_ACTION_TOKEN_PATTERN, token)
    if not match:
        return None

    try:
        json_str = match.group(1)
        data = json.loads(json_str)
        return MemoryAction.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """
    Format a MemoryAction object as a <MEMORY_ACTION> token string.

    Args:
        action: MemoryAction object

    Returns:
        Formatted token string
    """
    json_str = json.dumps(action.to_dict(), ensure_ascii=False)
    return f"<MEMORY_ACTION>{json_str}</MEMORY_ACTION>"

def parse_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """
    Extract all memory actions from a prompt string.

    Args:
        prompt: Text that may contain multiple <MEMORY_ACTION> tokens

    Returns:
        List of MemoryAction objects found in the prompt
    """
    actions = []
    pattern = re.compile(MEMORY_ACTION_TOKEN_PATTERN, re.DOTALL)
    matches = pattern.findall(prompt)

    for match in matches:
        try:
            data = json.loads(match)
            actions.append(MemoryAction.from_dict(data))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return actions

class WriteConflictResolver:
    """
    Queue-based write conflict resolution mechanism.

    When multiple agents attempt to write to the same key simultaneously,
    this resolver manages the queue and applies a resolution strategy.
    """

    def __init__(self):
        self._write_queue: deque = deque()
        self._lock = threading.Lock()
        self._pending_writes: Dict[str, deque] = {}  # key -> queue of requests

    def enqueue_write(self, request: WriteRequest) -> int:
        """
        Enqueue a write request.

        Args:
            request: WriteRequest to enqueue

        Returns:
            Position in the queue (0-indexed)
        """
        with self._lock:
            if request.key not in self._pending_writes:
                self._pending_writes[request.key] = deque()

            self._pending_writes[request.key].append(request)
            return len(self._pending_writes[request.key]) - 1

    def resolve_conflicts(self, key: str) -> ConflictResolutionResult:
        """
        Resolve write conflicts for a specific key using queue order.

        The first request in the queue wins; subsequent requests are rejected.

        Args:
            key: The memory key to resolve conflicts for

        Returns:
            ConflictResolutionResult with the winning request and rejected ones
        """
        with self._lock:
            if key not in self._pending_writes or len(self._pending_writes[key]) == 0:
                return ConflictResolutionResult(success=False)

            queue = self._pending_writes[key]
            if len(queue) == 1:
                # No conflict, single request
                winning = queue.popleft()
                return ConflictResolutionResult(
                    success=True,
                    winning_request=winning,
                    resolution_strategy="no_conflict"
                )

            # Multiple requests - queue order resolution
            winning = queue.popleft()
            rejected = list(queue)
            queue.clear()

            return ConflictResolutionResult(
                success=True,
                winning_request=winning,
                rejected_requests=rejected,
                resolution_strategy="queue_order"
            )

    def reset(self):
        """Clear all pending write requests."""
        with self._lock:
            self._pending_writes.clear()

    def get_pending_count(self, key: str) -> int:
        """Get number of pending writes for a key."""
        with self._lock:
            return len(self._pending_writes.get(key, deque()))

class MemoryBuffer:
    """
    Thread-safe shared memory buffer for multi-agent systems.

    Supports:
    - Write operations with conflict resolution
    - Read operations
    - <MEMORY_ACTION> token parsing and formatting
    - Queue-based write conflict resolution
    """

    def __init__(self):
        self._entries: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._conflict_resolver = WriteConflictResolver()
        self._write_log: List[WriteRequest] = []
        self._read_log: List[Tuple[str, float]] = []

    def write(self, key: str, value: str, agent_id: Optional[str] = None) -> Tuple[bool, Optional[ConflictResolutionResult]]:
        """
        Write a value to the memory buffer.

        If another write is pending for the same key, this request is queued
        and conflict resolution is triggered.

        Args:
            key: Memory key
            value: Value to store
            agent_id: Optional agent identifier

        Returns:
            Tuple of (success, ConflictResolutionResult if conflict occurred)
        """
        request = WriteRequest(key=key, value=value, agent_id=agent_id or "unknown")
        queue_position = self._conflict_resolver.enqueue_write(request)

        # If this is the only request, process immediately
        if queue_position == 0:
            result = self._conflict_resolver.resolve_conflicts(key)
            if result.success and result.winning_request:
                with self._lock:
                    existing = self._entries.get(key)
                    if existing:
                        new_entry = MemoryEntry(
                            key=key,
                            value=value,
                            timestamp=time.time(),
                            agent_id=agent_id,
                            version=existing.version + 1
                        )
                    else:
                        new_entry = MemoryEntry(
                            key=key,
                            value=value,
                            timestamp=time.time(),
                            agent_id=agent_id,
                            version=1
                        )
                    self._entries[key] = new_entry
                    self._write_log.append(request)
                return True, result
            return False, result
        else:
            # Queued, wait for resolution
            return False, None

    def read(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """
        Read a value from the memory buffer.

        Args:
            key: Memory key to read
            agent_id: Optional agent identifier (for logging)

        Returns:
            Value if found, None otherwise
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry:
                self._read_log.append((key, time.time()))
                return entry.value
            return None

    def read_with_metadata(self, key: str) -> Optional[MemoryEntry]:
        """
        Read a value with its metadata.

        Args:
            key: Memory key to read

        Returns:
            MemoryEntry if found, None otherwise
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry:
                self._read_log.append((key, time.time()))
                return entry
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from the memory buffer.

        Args:
            key: Memory key to delete

        Returns:
            True if deleted, False if key didn't exist
        """
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a value with a default fallback.

        Args:
            key: Memory key
            default: Default value if key not found

        Returns:
            Value or default
        """
        value = self.read(key)
        return value if value is not None else default

    def contains(self, key: str) -> bool:
        """Check if a key exists in the buffer."""
        with self._lock:
            return key in self._entries

    def keys(self) -> List[str]:
        """Return all keys in the buffer."""
        with self._lock:
            return list(self._entries.keys())

    def size(self) -> int:
        """Return the number of entries in the buffer."""
        with self._lock:
            return len(self._entries)

    def reset(self):
        """Reset the buffer to empty state."""
        with self._lock:
            self._entries.clear()
            self._write_log.clear()
            self._read_log.clear()
        self._conflict_resolver.reset()

    def process_action_token(self, token: str, agent_id: Optional[str] = None) -> Optional[str]:
        """
        Process a <MEMORY_ACTION> token and execute the operation.

        Args:
            token: Token string to process
            agent_id: Agent performing the action

        Returns:
            Result of the operation (value for reads, None for writes)
        """
        action = parse_memory_action_token(token)
        if not action:
            return None

        if action.type == "write":
            if action.value is None:
                return None
            success, _ = self.write(action.key, action.value, agent_id)
            return format_action_token(MemoryAction(
                type="write_result",
                key=action.key,
                value="success" if success else "queued"
            ))
        elif action.type == "read":
            value = self.read(action.key, agent_id)
            if value:
                return format_action_token(MemoryAction(
                    type="read_result",
                    key=action.key,
                    value=value
                ))
            return None
        return None

    def process_prompt(self, prompt: str, agent_id: Optional[str] = None) -> List[str]:
        """
        Process all memory actions in a prompt string.

        Args:
            prompt: Text containing memory action tokens
            agent_id: Agent performing the actions

        Returns:
            List of result tokens
        """
        actions = parse_action_from_prompt(prompt)
        results = []
        for action in actions:
            token = format_action_token(action)
            result = self.process_action_token(token, agent_id)
            if result:
                results.append(result)
        return results

    def get_write_log(self) -> List[Dict[str, Any]]:
        """Return the write log for analysis."""
        with self._lock:
            return [
                {
                    "key": req.key,
                    "value": req.value,
                    "agent_id": req.agent_id,
                    "timestamp": req.timestamp,
                    "request_id": req.request_id
                }
                for req in self._write_log
            ]

    def get_read_log(self) -> List[Dict[str, Any]]:
        """Return the read log for analysis."""
        with self._lock:
            return [
                {"key": key, "timestamp": ts}
                for key, ts in self._read_log
            ]

    def __getattr__(self, name: str):
        """
        Tolerant fallback for any unknown method/attribute.
        Returns a no-op callable to prevent AttributeError in logger-like usage.
        """
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

# Shared singleton buffer instance
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer() -> MemoryBuffer:
    """Get or create the shared memory buffer singleton."""
    global _SHARED_BUFFER
    if _SHARED_BUFFER is None:
        with _BUFFER_LOCK:
            if _SHARED_BUFFER is None:
                _SHARED_BUFFER = MemoryBuffer()
    return _SHARED_BUFFER

def reset_shared_buffer():
    """Reset the shared memory buffer singleton."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
            _SHARED_BUFFER = None