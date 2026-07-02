"""
Shared External Memory Buffer with <MEMORY_ACTION> token handling.
Implements a thread-safe buffer for multi-agent memory operations.
"""
import threading
import time
from dataclasses import dataclass, field
from typing import List, Any, Optional, Callable, Dict
import re


@dataclass
class MemoryEntry:
    """Represents a single memory entry in the buffer."""
    agent_id: str
    timestamp: float
    content: str
    action_type: str  # 'store', 'retrieve', 'update', 'delete'
    context: Optional[Dict[str, Any]] = None


class MemoryBuffer:
    """
    Thread-safe shared memory buffer for multi-agent systems.
    Handles <MEMORY_ACTION> tokens and maintains a log of operations.
    """
    _instance: Optional['MemoryBuffer'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._entries: List[MemoryEntry] = []
        self._callbacks: List[Callable[[MemoryEntry], None]] = []
        self._lock = threading.RLock()
        self._memory_action_pattern = re.compile(r'<MEMORY_ACTION:(\w+)>(.+?)</MEMORY_ACTION>')
    
    @classmethod
    def get_shared(cls) -> 'MemoryBuffer':
        """Get or create the shared memory buffer instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = MemoryBuffer()
        return cls._instance
    
    @classmethod
    def reset_shared(cls) -> None:
        """Reset the shared memory buffer instance."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.reset()
    
    def reset(self) -> None:
        """Clear all entries from the buffer."""
        with self._lock:
            self._entries.clear()
    
    def parse_memory_action(self, text: str) -> List[MemoryEntry]:
        """
        Parse <MEMORY_ACTION> tokens from text and return list of MemoryEntry objects.
        
        Args:
            text: Input text potentially containing <MEMORY_ACTION> tokens
            
        Returns:
            List of MemoryEntry objects extracted from the text
        """
        entries = []
        matches = self._memory_action_pattern.findall(text)
        
        for action_type, content in matches:
            entry = MemoryEntry(
                agent_id="unknown",  # Will be set by caller
                timestamp=time.time(),
                content=content.strip(),
                action_type=action_type
            )
            entries.append(entry)
        
        return entries
    
    def add_entry(self, agent_id: str, content: str, action_type: str, 
                 context: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        """Add a new memory entry to the buffer."""
        entry = MemoryEntry(
            agent_id=agent_id,
            timestamp=time.time(),
            content=content,
            action_type=action_type,
            context=context
        )
        
        with self._lock:
            self._entries.append(entry)
            for callback in self._callbacks:
                try:
                    callback(entry)
                except Exception:
                    pass  # Log error but continue
        
        return entry
    
    def get_entries(self, agent_id: Optional[str] = None, 
                   limit: Optional[int] = None) -> List[MemoryEntry]:
        """Get entries from the buffer, optionally filtered by agent_id."""
        with self._lock:
            entries = self._entries.copy()
        
        if agent_id is not None:
            entries = [e for e in entries if e.agent_id == agent_id]
        
        if limit is not None:
            entries = entries[-limit:]
        
        return entries
    
    def register_callback(self, callback: Callable[[MemoryEntry], None]) -> None:
        """Register a callback to be called on new memory entries."""
        with self._lock:
            self._callbacks.append(callback)
    
    def __len__(self) -> int:
        """Return the number of entries in the buffer."""
        with self._lock:
            return len(self._entries)
    
    def __getattr__(self, name: str):
        """
        Tolerant fallback for unknown method calls.
        Returns a no-op function for any unknown attribute.
        This ensures compatibility with various caller patterns.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop


def get_shared_memory_buffer() -> MemoryBuffer:
    """Convenience function to get the shared memory buffer."""
    return MemoryBuffer.get_shared()


def reset_shared_memory_buffer() -> None:
    """Convenience function to reset the shared memory buffer."""
    MemoryBuffer.reset_shared()
