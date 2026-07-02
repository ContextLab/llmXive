import threading
from dataclasses import dataclass, field
from typing import List, Any, Optional, Callable
import time
import re

@dataclass
class MemoryEntry:
    """A single entry in the shared memory buffer."""
    timestamp: float
    agent_id: str
    action_type: str  # 'store', 'retrieve', 'update'
    content: str
    cue: Optional[str] = None
    success: bool = True

def parse_memory_action(text: str) -> Optional[dict]:
    """
    Parse a <MEMORY_ACTION> token string into a structured dict.
    Expected format: <MEMORY_ACTION type="store" cue="..." content="...">
    """
    pattern = r'<MEMORY_ACTION\s+type="(\w+)"\s+cue="([^"]*)"\s+content="([^"]*)">'
    match = re.match(pattern, text)
    if match:
        return {
            'type': match.group(1),
            'cue': match.group(2),
            'content': match.group(3)
        }
    return None

class MemoryBuffer:
    """
    Shared external memory buffer for multi-agent transactive memory.
    Implements a thread-safe queue of memory entries with <MEMORY_ACTION> token handling.
    """
    def __init__(self, max_entries: int = 10000):
        self._entries: List[MemoryEntry] = []
        self._lock = threading.RLock()
        self._max_entries = max_entries
        self._callbacks: List[Callable[[MemoryEntry], None]] = []

    def add_entry(self, agent_id: str, action_type: str, content: str, cue: Optional[str] = None) -> MemoryEntry:
        """Add a new memory entry to the buffer."""
        with self._lock:
            entry = MemoryEntry(
                timestamp=time.time(),
                agent_id=agent_id,
                action_type=action_type,
                content=content,
                cue=cue,
                success=True
            )
            if len(self._entries) >= self._max_entries:
                self._entries.pop(0)
            self._entries.append(entry)
            for cb in self._callbacks:
                try:
                    cb(entry)
                except Exception:
                    pass
            return entry

    def get_entries(self, agent_id: Optional[str] = None, limit: Optional[int] = None) -> List[MemoryEntry]:
        """Retrieve entries, optionally filtered by agent_id."""
        with self._lock:
            entries = self._entries
            if agent_id:
                entries = [e for e in entries if e.agent_id == agent_id]
            if limit:
                entries = entries[-limit:]
            return list(entries)

    def search_by_cue(self, cue: str) -> List[MemoryEntry]:
        """Retrieve entries matching a specific cue."""
        with self._lock:
            return [e for e in self._entries if e.cue == cue]

    def reset(self):
        """Clear all entries from the buffer."""
        with self._lock:
            self._entries.clear()

    def register_callback(self, callback: Callable[[MemoryEntry], None]):
        """Register a callback to be called on new entries."""
        with self._lock:
            self._callbacks.append(callback)

    def __getattr__(self, name: str):
        """
        Tolerant fallback for logger-style calls or unknown attributes.
        Returns a no-op callable to prevent AttributeError on dynamic calls.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

# Singleton pattern for shared memory buffer
_shared_buffer_instance: Optional[MemoryBuffer] = None
_buffer_lock = threading.Lock()

def get_shared_memory_buffer(max_entries: int = 10000) -> MemoryBuffer:
    """Get the singleton shared memory buffer instance."""
    global _shared_buffer_instance
    if _shared_buffer_instance is None:
        with _buffer_lock:
            if _shared_buffer_instance is None:
                _shared_buffer_instance = MemoryBuffer(max_entries=max_entries)
    return _shared_buffer_instance

def reset_shared_memory_buffer():
    """Reset the singleton shared memory buffer."""
    global _shared_buffer_instance
    with _buffer_lock:
        if _shared_buffer_instance is not None:
            _shared_buffer_instance.reset()
            _shared_buffer_instance = None
