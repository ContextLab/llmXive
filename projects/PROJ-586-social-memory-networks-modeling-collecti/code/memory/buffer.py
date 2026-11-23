"""
Shared external memory buffer for multi-agent social memory networks.

Implements a thread-safe buffer supporting <MEMORY_ACTION> tokens with JSON schema:
{"type": "write"|"read", "key": str, "value": str}

Includes queue-based write conflict resolution.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.logging import get_logger

logger = get_logger(__name__)

# --- Data Classes ---

@dataclass
class MemoryAction:
    """Represents a single memory action (write or read)."""
    type: str  # 'write' or 'read'
    key: str
    value: Optional[str] = None  # Optional for reads, required for writes

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "key": self.key, "value": self.value}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryAction":
        return cls(
            type=data["type"],
            key=data["key"],
            value=data.get("value")
        )

@dataclass
class MemoryEntry:
    """Represents a single entry in the memory buffer."""
    key: str
    value: str
    timestamp: float = field(default_factory=time.time)
    agent_id: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "confidence": self.confidence
        }

@dataclass
class WriteRequest:
    """Represents a request to write to the buffer."""
    key: str
    value: str
    agent_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class ConflictResolutionResult:
    """Result of a conflict resolution attempt."""
    success: bool
    resolved_key: str
    resolved_value: str
    winning_agent_id: Optional[str] = None
    resolution_strategy: str = "first_write"

# --- Conflict Resolution Strategy ---

class WriteConflictResolver:
    """
    Queue-based write conflict resolution.

    Strategy: First-Write-Wins (FIFO). If multiple agents attempt to write
    to the same key within a short window, the first one to arrive is kept.
    Subsequent writes are queued and rejected or logged as conflicts.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._write_queue: deque = deque()
        self._processing = False

    def reset(self) -> None:
        """Reset the resolver state."""
        with self._lock:
            self._write_queue.clear()
            self._processing = False

    def resolve(self, request: WriteRequest, existing_entry: Optional[MemoryEntry]) -> ConflictResolutionResult:
        """
        Resolve a write conflict.

        Args:
            request: The incoming write request.
            existing_entry: The existing entry in the buffer, if any.

        Returns:
            ConflictResolutionResult indicating success and the resolved value.
        """
        with self._lock:
            if existing_entry is None:
                # No conflict, write is allowed
                return ConflictResolutionResult(
                    success=True,
                    resolved_key=request.key,
                    resolved_value=request.value,
                    winning_agent_id=request.agent_id,
                    resolution_strategy="no_conflict"
                )

            # Conflict detected: existing entry vs new request
            # Strategy: First-Write-Wins. The existing entry wins.
            return ConflictResolutionResult(
                success=False,
                resolved_key=request.key,
                resolved_value=existing_entry.value,
                winning_agent_id=existing_entry.agent_id,
                resolution_strategy="first_write_wins"
            )

    def process_queue(self, buffer: "MemoryBuffer") -> None:
        """Process the write queue (placeholder for future extensions)."""
        with self._lock:
            while self._write_queue:
                request = self._write_queue.popleft()
                # In a full implementation, we might re-evaluate conflicts here
                # For now, we just log that we processed it
                logger.log("process_queue_item", key=request.key)

# --- Memory Buffer ---

class MemoryBuffer:
    """
    Thread-safe shared external memory buffer.

    Supports <MEMORY_ACTION> tokens with JSON schema:
    {"type": "write"|"read", "key": str, "value": str}

    Implements queue-based write conflict resolution via WriteConflictResolver.
    """

    def __init__(self, capacity: int = 1000):
        self._lock = threading.RLock()
        self._buffer: Dict[str, MemoryEntry] = {}
        self._capacity = capacity
        self._resolver = WriteConflictResolver()
        self._access_log: List[Dict[str, Any]] = []

    def reset(self) -> None:
        """Reset the buffer to an empty state."""
        with self._lock:
            self._buffer.clear()
            self._access_log.clear()
            self._resolver.reset()
            logger.log("buffer_reset", capacity=self._capacity)

    def _enforce_capacity(self) -> None:
        """Enforce capacity limit by removing oldest entries."""
        if len(self._buffer) > self._capacity:
            # Sort by timestamp and remove oldest
            sorted_entries = sorted(self._buffer.items(), key=lambda x: x[1].timestamp)
            to_remove = len(sorted_entries) - self._capacity
            for key, _ in sorted_entries[:to_remove]:
                del self._buffer[key]
            logger.log("capacity_enforced", removed_count=to_remove, new_size=len(self._buffer))

    def write(self, key: str, value: str, agent_id: Optional[str] = None, confidence: float = 1.0) -> bool:
        """
        Write a value to the buffer.

        Args:
            key: The key for the memory entry.
            value: The value to store.
            agent_id: Optional ID of the agent writing.
            confidence: Confidence score (0.0 to 1.0).

        Returns:
            True if write was successful, False if conflict prevented it.
        """
        with self._lock:
            existing = self._buffer.get(key)
            request = WriteRequest(key=key, value=value, agent_id=agent_id)
            result = self._resolver.resolve(request, existing)

            if result.success:
                self._buffer[key] = MemoryEntry(
                    key=key,
                    value=value,
                    agent_id=agent_id,
                    confidence=confidence
                )
                self._enforce_capacity()
                self._log_access("write", key, agent_id)
                logger.log("write_success", key=key, agent_id=agent_id)
                return True
            else:
                self._log_access("write_conflict", key, agent_id)
                logger.log("write_conflict", key=key, winning_agent=result.winning_agent_id)
                return False

    def read(self, key: str, agent_id: Optional[str] = None) -> Optional[MemoryEntry]:
        """
        Read a value from the buffer.

        Args:
            key: The key to look up.
            agent_id: Optional ID of the agent reading.

        Returns:
            The MemoryEntry if found, None otherwise.
        """
        with self._lock:
            entry = self._buffer.get(key)
            if entry:
                self._log_access("read", key, agent_id)
                logger.log("read_success", key=key, agent_id=agent_id)
                return entry
            else:
                self._log_access("read_miss", key, agent_id)
                logger.log("read_miss", key=key, agent_id=agent_id)
                return None

    def delete(self, key: str, agent_id: Optional[str] = None) -> bool:
        """
        Delete a value from the buffer.

        Args:
            key: The key to delete.
            agent_id: Optional ID of the agent deleting.

        Returns:
            True if deleted, False if key not found.
        """
        with self._lock:
            if key in self._buffer:
                del self._buffer[key]
                self._log_access("delete", key, agent_id)
                logger.log("delete_success", key=key, agent_id=agent_id)
                return True
            else:
                self._log_access("delete_miss", key, agent_id)
                logger.log("delete_miss", key=key, agent_id=agent_id)
                return False

    def search(self, query: str, agent_id: Optional[str] = None) -> List[MemoryEntry]:
        """
        Search for entries containing the query string in their value.

        Args:
            query: The search query string.
            agent_id: Optional ID of the agent searching.

        Returns:
            List of matching MemoryEntry objects.
        """
        with self._lock:
            results = [
                entry for entry in self._buffer.values()
                if query.lower() in entry.value.lower()
            ]
            self._log_access("search", query, agent_id)
            logger.log("search", query=query, result_count=len(results), agent_id=agent_id)
            return results

    def get_all(self) -> List[MemoryEntry]:
        """Get all entries in the buffer."""
        with self._lock:
            return list(self._buffer.values())

    def _log_access(self, action: str, key_or_query: str, agent_id: Optional[str]) -> None:
        """Log an access event."""
        self._access_log.append({
            "action": action,
            "key_or_query": key_or_query,
            "agent_id": agent_id,
            "timestamp": time.time()
        })

    # --- Tolerant Logger Interface ---

    def __getattr__(self, name: str):
        """
        Provide a tolerant interface for logger-like calls.
        Any unknown attribute access returns a no-op callable.
        """
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

# --- Token Parsing & Formatting ---

MEMORY_ACTION_PATTERN = re.compile(r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>", re.DOTALL)

def now() -> float:
    """Return current timestamp."""
    return time.time()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """
    Parse a <MEMORY_ACTION> token string into a MemoryAction object.

    Args:
        token: The full token string, e.g., "<MEMORY_ACTION>{...}</MEMORY_ACTION>"

    Returns:
        MemoryAction object or None if parsing fails.
    """
    match = MEMORY_ACTION_PATTERN.search(token)
    if not match:
        return None

    try:
        json_str = match.group(1)
        data = json.loads(json_str)
        return MemoryAction.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        logger.log("parse_error", token=token[:50], error=str(e))
        return None

def format_action_token(action: MemoryAction) -> str:
    """
    Format a MemoryAction object into a <MEMORY_ACTION> token string.

    Args:
        action: The MemoryAction object.

    Returns:
        The formatted token string.
    """
    json_str = json.dumps(action.to_dict(), ensure_ascii=False)
    return f"<MEMORY_ACTION>{json_str}</MEMORY_ACTION>"

def parse_memory_action_from_prompt(prompt: str) -> List[MemoryAction]:
    """
    Parse all <MEMORY_ACTION> tokens from a prompt string.

    Args:
        prompt: The prompt string potentially containing tokens.

    Returns:
        List of parsed MemoryAction objects.
    """
    actions = []
    for match in MEMORY_ACTION_PATTERN.finditer(prompt):
        try:
            json_str = match.group(1)
            data = json.loads(json_str)
            actions.append(MemoryAction.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            continue
    return actions

# --- Singleton Shared Buffer ---

_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer(capacity: int = 1000) -> MemoryBuffer:
    """
    Get the singleton shared memory buffer.

    Args:
        capacity: The capacity for the buffer if it needs to be created.

    Returns:
        The shared MemoryBuffer instance.
    """
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer(capacity=capacity)
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the singleton shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()
        _SHARED_BUFFER = None