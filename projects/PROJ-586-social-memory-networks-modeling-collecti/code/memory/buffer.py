"""
Shared memory buffer implementation with <MEMORY_ACTION> token handling.
"""
import threading
import time
from dataclasses import dataclass, field
from typing import List, Any, Optional, Callable, Dict
import re

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    timestamp: float
    agent_id: str
    action_type: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

def parse_memory_action(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a <MEMORY_ACTION> token from text.

    Args:
        text: Text containing potential memory action

    Returns:
        Parsed action dict or None if not found
    """
    pattern = r'<MEMORY_ACTION\s+type="([^"]+)"\s+content="([^"]*)"\s*(metadata="([^"]*)")?\s*>'
    match = re.search(pattern, text)
    if match:
        action = {
            'type': match.group(1),
            'content': match.group(2),
            'metadata': {}
        }
        if match.group(4):
            try:
                import json
                action['metadata'] = json.loads(match.group(4))
            except (json.JSONDecodeError, TypeError):
                action['metadata'] = {}
        return action
    return None

class MemoryBuffer:
    """
    Thread-safe shared memory buffer for multi-agent systems.
    Supports <MEMORY_ACTION> token handling.
    """

    _instance: Optional['MemoryBuffer'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._entries: List[MemoryEntry] = []
        self._callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def store(self, agent_id: str, action_type: str, content: Any, metadata: Optional[Dict] = None) -> MemoryEntry:
        """Store a memory entry."""
        entry = MemoryEntry(
            timestamp=time.time(),
            agent_id=agent_id,
            action_type=action_type,
            content=content,
            metadata=metadata or {}
        )
        with self._lock:
            self._entries.append(entry)
            self._notify_callbacks(action_type, entry)
        return entry

    def retrieve(self, agent_id: Optional[str] = None, action_type: Optional[str] = None, limit: int = 100) -> List[MemoryEntry]:
        """Retrieve memory entries with optional filters."""
        with self._lock:
            results = self._entries.copy()

        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        if action_type:
            results = [e for e in results if e.action_type == action_type]

        return results[-limit:]

    def clear(self):
        """Clear all entries."""
        with self._lock:
            self._entries.clear()

    def reset(self):
        """Reset the buffer (alias for clear)."""
        self.clear()

    def register_callback(self, action_type: str, callback: Callable[[MemoryEntry], None]):
        """Register a callback for a specific action type."""
        with self._lock:
            if action_type not in self._callbacks:
                self._callbacks[action_type] = []
            self._callbacks[action_type].append(callback)

    def _notify_callbacks(self, action_type: str, entry: MemoryEntry):
        """Notify all callbacks for an action type."""
        with self._lock:
            callbacks = self._callbacks.get(action_type, []).copy()

        for callback in callbacks:
            try:
                callback(entry)
            except Exception:
                pass  # Don't let callback errors break the buffer

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def __getattr__(self, name: str):
        """
        Fallback for unknown attributes to support logger-style calls.
        Returns a no-op callable for any unknown method name.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_shared_memory_buffer() -> MemoryBuffer:
    """Get or create the shared memory buffer instance."""
    if MemoryBuffer._instance is None:
        with MemoryBuffer._lock:
            if MemoryBuffer._instance is None:
                MemoryBuffer._instance = MemoryBuffer()
    return MemoryBuffer._instance

def reset_shared_memory_buffer():
    """Reset the shared memory buffer."""
    if MemoryBuffer._instance is not None:
        MemoryBuffer._instance.reset()
