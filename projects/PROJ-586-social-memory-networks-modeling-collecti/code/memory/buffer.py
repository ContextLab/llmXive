"""
Shared external memory buffer for multi-agent systems.

This module implements a thread-safe memory buffer that agents can use to
store, retrieve, and share information across the agent population.
Memory operations are triggered via <MEMORY_ACTION> tokens in agent outputs.

FR-003: Implement shared external memory buffer with <MEMORY_ACTION> token handling
"""

import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import time
import hashlib
import json
import re


class MemoryAction(Enum):
    """Types of memory actions that can be performed."""
    STORE = "store"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    QUERY = "query"


@dataclass
class MemoryEntry:
    """A single memory entry in the buffer."""
    id: str
    content: str
    creator_agent: str
    timestamp: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "creator_agent": self.creator_agent,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class MemoryActionRequest:
    """A parsed memory action request from agent output."""
    action: MemoryAction
    params: Dict[str, Any]
    raw_content: str


@dataclass
class MemoryActionResult:
    """Result of executing a memory action."""
    success: bool
    data: Any = None
    error: Optional[str] = None


class MemoryBuffer:
    """
    Thread-safe shared memory buffer for multi-agent systems.

    This buffer allows multiple agents to store and retrieve memories
    in a shared space, enabling collective remembering. The buffer
    supports LRU eviction when capacity is exceeded.

    Args:
        max_entries: Maximum number of entries before eviction (default: 10000)
        max_tokens: Maximum total tokens before eviction (default: 1000000)
        eviction_policy: "lru" or "lfu" for eviction strategy
    """

    def __init__(
        self,
        max_entries: int = 10000,
        max_tokens: int = 1000000,
        eviction_policy: str = "lru",
    ):
        self._storage: Dict[str, MemoryEntry] = {}
        self._lock = threading.RLock()
        self._access_order: deque = deque()  # For LRU tracking
        self._total_tokens = 0
        self._max_entries = max_entries
        self._max_tokens = max_tokens
        self._eviction_policy = eviction_policy

    @property
    def size(self) -> int:
        """Current number of entries in buffer."""
        with self._lock:
            return len(self._storage)

    @property
    def total_tokens(self) -> int:
        """Estimated total tokens in buffer."""
        with self._lock:
            return self._total_tokens

    def _estimate_tokens(self, content: str) -> int:
        """Estimate token count for content (approx 4 chars per token)."""
        return len(content) // 4

    def _generate_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique ID for a memory entry."""
        combined = content + str(metadata) + str(time.time())
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def store(
        self,
        content: str,
        creator_agent: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        Store a new memory entry in the buffer.

        Args:
            content: The memory content to store
            creator_agent: ID of the agent creating this memory
            tags: Optional list of tags for categorization
            metadata: Optional additional metadata

        Returns:
            The created MemoryEntry
        """
        with self._lock:
            entry_id = self._generate_id(content, metadata or {})
            entry = MemoryEntry(
                id=entry_id,
                content=content,
                creator_agent=creator_agent,
                timestamp=time.time(),
                tags=tags or [],
                metadata=metadata or {},
            )

            # Evict if at capacity
            self._evict_if_needed()

            self._storage[entry_id] = entry
            self._access_order.append(entry_id)
            self._total_tokens += self._estimate_tokens(content)

            return entry

    def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Retrieve a memory entry by ID.

        Args:
            memory_id: The ID of the memory to retrieve

        Returns:
            The MemoryEntry if found, None otherwise
        """
        with self._lock:
            if memory_id not in self._storage:
                return None

            entry = self._storage[memory_id]
            entry.access_count += 1
            entry.last_accessed = time.time()

            # Update LRU order
            if memory_id in self._access_order:
                self._access_order.remove(memory_id)
                self._access_order.append(memory_id)

            return entry

    def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MemoryEntry]:
        """
        Update an existing memory entry.

        Args:
            memory_id: The ID of the memory to update
            content: New content (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)

        Returns:
            The updated MemoryEntry if found, None otherwise
        """
        with self._lock:
            if memory_id not in self._storage:
                return None

            entry = self._storage[memory_id]

            if content is not None:
                old_tokens = self._estimate_tokens(entry.content)
                entry.content = content
                self._total_tokens = self._total_tokens - old_tokens + self._estimate_tokens(content)

            if tags is not None:
                entry.tags = tags

            if metadata is not None:
                entry.metadata = metadata

            entry.last_accessed = time.time()
            entry.access_count += 1

            return entry

    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory entry by ID.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if memory_id not in self._storage:
                return False

            entry = self._storage[memory_id]
            self._total_tokens -= self._estimate_tokens(entry.content)
            del self._storage[memory_id]

            if memory_id in self._access_order:
                self._access_order.remove(memory_id)

            return True

    def query(
        self,
        query_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        creator_agent: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        """
        Query memories with optional filters.

        Args:
            query_text: Search for this text in content
            tags: Filter by these tags (any match)
            creator_agent: Filter by creator agent ID
            limit: Maximum results to return

        Returns:
            List of matching MemoryEntry objects
        """
        with self._lock:
            results = []

            for entry in self._storage.values():
                # Filter by query text
                if query_text and query_text.lower() not in entry.content.lower():
                    continue

                # Filter by tags
                if tags and not any(tag in entry.tags for tag in tags):
                    continue

                # Filter by creator
                if creator_agent and entry.creator_agent != creator_agent:
                    continue

                results.append(entry)

                if len(results) >= limit:
                    break

            return results

    def _evict_if_needed(self) -> int:
        """Evict entries if buffer is at capacity. Returns number evicted."""
        evicted = 0

        while (
            len(self._storage) >= self._max_entries
            or self._total_tokens >= self._max_tokens
        ):
            if not self._access_order:
                break

            # LRU: remove oldest accessed
            oldest_id = self._access_order.popleft()

            if oldest_id not in self._storage:
                continue

            entry = self._storage[oldest_id]
            self._total_tokens -= self._estimate_tokens(entry.content)
            del self._storage[oldest_id]
            evicted += 1

        return evicted

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._storage.clear()
            self._access_order.clear()
            self._total_tokens = 0

    def get_all_entries(self) -> List[MemoryEntry]:
        """Get all entries in the buffer."""
        with self._lock:
            return list(self._storage.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        with self._lock:
            return {
                "size": len(self._storage),
                "max_entries": self._max_entries,
                "total_tokens": self._total_tokens,
                "max_tokens": self._max_tokens,
                "eviction_policy": self._eviction_policy,
            }


# Global shared memory buffer instance
_global_buffer: Optional[MemoryBuffer] = None
_buffer_lock = threading.Lock()


def get_shared_memory_buffer() -> MemoryBuffer:
    """Get or create the global shared memory buffer."""
    global _global_buffer
    with _buffer_lock:
        if _global_buffer is None:
            _global_buffer = MemoryBuffer()
        return _global_buffer


def reset_shared_memory_buffer() -> None:
    """Reset the global shared memory buffer."""
    global _global_buffer
    with _buffer_lock:
        if _global_buffer is not None:
            _global_buffer.clear()
            _global_buffer = None


MEMORY_ACTION_PATTERN = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"


def parse_memory_action(content: str) -> Optional[MemoryActionRequest]:
    """
    Parse a memory action from agent output content.

    Args:
        content: The agent output containing <MEMORY_ACTION> token

    Returns:
        MemoryActionRequest if valid action found, None otherwise
    """
    match = re.search(MEMORY_ACTION_PATTERN, content, re.DOTALL)
    if not match:
        return None

    action_content = match.group(1).strip()

    try:
        action_data = json.loads(action_content)
        action_type = action_data.get("action", "").lower()
        params = action_data.get("params", {})

        action = MemoryAction(action_type)
        return MemoryActionRequest(
            action=action,
            params=params,
            raw_content=action_content,
        )
    except (json.JSONDecodeError, ValueError) as e:
        return None


def execute_memory_action(
    request: MemoryActionRequest,
    buffer: Optional[MemoryBuffer] = None,
) -> MemoryActionResult:
    """
    Execute a parsed memory action on the buffer.

    Args:
        request: The parsed MemoryActionRequest
        buffer: Optional buffer instance (uses global if not provided)

    Returns:
        MemoryActionResult with success status and data/error
    """
    if buffer is None:
        buffer = get_shared_memory_buffer()

    try:
        if request.action == MemoryAction.STORE:
            content = request.params.get("content")
            creator = request.params.get("creator_agent")
            tags = request.params.get("tags", [])
            metadata = request.params.get("metadata", {})

            if not content or not creator:
                return MemoryActionResult(
                    success=False,
                    error="STORE requires 'content' and 'creator_agent'",
                )

            entry = buffer.store(content, creator, tags, metadata)
            return MemoryActionResult(
                success=True,
                data={"memory_id": entry.id},
            )

        elif request.action == MemoryAction.RETRIEVE:
            memory_id = request.params.get("memory_id")
            if not memory_id:
                return MemoryActionResult(
                    success=False,
                    error="RETRIEVE requires 'memory_id'",
                )

            entry = buffer.retrieve(memory_id)
            if entry is None:
                return MemoryActionResult(
                    success=False,
                    error=f"Memory not found: {memory_id}",
                )

            return MemoryActionResult(
                success=True,
                data=entry.to_dict(),
            )

        elif request.action == MemoryAction.UPDATE:
            memory_id = request.params.get("memory_id")
            content = request.params.get("content")

            if not memory_id:
                return MemoryActionResult(
                    success=False,
                    error="UPDATE requires 'memory_id'",
                )

            entry = buffer.update(
                memory_id,
                content=content,
                tags=request.params.get("tags"),
                metadata=request.params.get("metadata"),
            )

            if entry is None:
                return MemoryActionResult(
                    success=False,
                    error=f"Memory not found: {memory_id}",
                )

            return MemoryActionResult(
                success=True,
                data=entry.to_dict(),
            )

        elif request.action == MemoryAction.DELETE:
            memory_id = request.params.get("memory_id")
            if not memory_id:
                return MemoryActionResult(
                    success=False,
                    error="DELETE requires 'memory_id'",
                )

            deleted = buffer.delete(memory_id)
            return MemoryActionResult(
                success=deleted,
                data={"deleted": deleted},
            )

        elif request.action == MemoryAction.QUERY:
            query_text = request.params.get("query_text")
            tags = request.params.get("tags", [])
            creator = request.params.get("creator_agent")
            limit = request.params.get("limit", 100)

            results = buffer.query(
                query_text=query_text,
                tags=tags if tags else None,
                creator_agent=creator,
                limit=limit,
            )

            return MemoryActionResult(
                success=True,
                data=[entry.to_dict() for entry in results],
            )

        else:
            return MemoryActionResult(
                success=False,
                error=f"Unknown action: {request.action}",
            )

    except Exception as e:
        return MemoryActionResult(success=False, error=str(e))


def handle_agent_output(
    output: str,
    buffer: Optional[MemoryBuffer] = None,
) -> Tuple[str, List[MemoryActionResult]]:
    """
    Process agent output and execute any memory actions found.

    Args:
        output: The full agent output string
        buffer: Optional buffer instance (uses global if not provided)

    Returns:
        Tuple of (cleaned_output_without_tokens, list of results)
    """
    if buffer is None:
        buffer = get_shared_memory_buffer()

    results = []

    # Find all memory action tokens
    matches = list(re.finditer(MEMORY_ACTION_PATTERN, output, re.DOTALL))

    if not matches:
        return output, results

    # Execute each action
    for match in matches:
        action_content = match.group(1).strip()
        request = parse_memory_action(f"<MEMORY_ACTION>{action_content}</MEMORY_ACTION>")

        if request:
            result = execute_memory_action(request, buffer)
            results.append(result)

    # Remove all memory action tokens from output
    cleaned_output = re.sub(MEMORY_ACTION_PATTERN, "", output, flags=re.DOTALL).strip()

    return cleaned_output, results
