import threading
from dataclasses import dataclass, field
from typing import List, Any, Optional
import time

@dataclass
class MemoryEntry:
    """Represents a single entry in the shared memory buffer."""
    timestamp: float
    agent_id: int
    action: str
    content: str
    context_window: Optional[int] = None

class MemoryBuffer:
    """
    Shared external memory buffer for multi-agent social memory experiments.
    Handles <MEMORY_ACTION> token parsing and thread-safe operations.
    """
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.entries: List[MemoryEntry] = []
        self._lock = threading.Lock()
        self.action_patterns = ["<MEMORY_ACTION>", "<MEM>", "<SAVE>", "<RETRIEVE>"]

    def add_entry(self, agent_id: int, action: str, content: str, context_window: Optional[int] = None) -> None:
        """Add a new memory entry to the buffer."""
        with self._lock:
            entry = MemoryEntry(
                timestamp=time.time(),
                agent_id=agent_id,
                action=action,
                content=content,
                context_window=context_window
            )
            self.entries.append(entry)
            # Enforce capacity
            if len(self.entries) > self.capacity:
                self.entries = self.entries[-self.capacity:]

    def get_recent(self, n: int = 10) -> List[MemoryEntry]:
        """Get the n most recent entries."""
        with self._lock:
            return self.entries[-n:] if n < len(self.entries) else self.entries.copy()

    def get_by_agent(self, agent_id: int, limit: Optional[int] = None) -> List[MemoryEntry]:
        """Get entries for a specific agent."""
        with self._lock:
            entries = [e for e in self.entries if e.agent_id == agent_id]
            if limit:
                entries = entries[-limit:]
            return entries

    def search(self, query: str) -> List[MemoryEntry]:
        """Search for entries containing the query string."""
        with self._lock:
            return [e for e in self.entries if query.lower() in e.content.lower()]

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self.entries.clear()

    def reset(self) -> None:
        """Reset the buffer to initial state (alias for clear for compatibility)."""
        self.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self.entries)

    def __repr__(self) -> str:
        return f"MemoryBuffer(entries={len(self)}, capacity={self.capacity})"

# Shared instance management for multi-process/thread scenarios
_shared_buffer: Optional[MemoryBuffer] = None
_buffer_lock = threading.Lock()

def get_shared_memory_buffer(capacity: int = 10000) -> MemoryBuffer:
    """Get or create the shared memory buffer instance."""
    global _shared_buffer
    with _buffer_lock:
        if _shared_buffer is None:
            _shared_buffer = MemoryBuffer(capacity=capacity)
        return _shared_buffer

def reset_shared_memory_buffer() -> None:
    """Reset the shared memory buffer."""
    global _shared_buffer
    with _buffer_lock:
        if _shared_buffer is not None:
            _shared_buffer.reset()
            _shared_buffer = None
