"""
Streaming Utilities (Task T008 / T022 Integration).

Provides StreamingBuffer and StreamingConfig to enforce memory limits
during feature extraction and data processing.
"""
from dataclasses import dataclass, field
from typing import List, Any, Optional, Generic, TypeVar
import gc
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class StreamingConfig:
    """Configuration for streaming operations."""
    max_memory_gb: float = 6.0
    chunk_size: int = 2000
    enable_gc: bool = True

@dataclass
class StreamingBuffer(Generic[T]):
    """
    A buffer that automatically flushes when a size threshold is reached.
    Used to keep memory usage under control.
    """
    config: StreamingConfig
    _buffer: List[T] = field(default_factory=list)
    
    @property
    def size(self) -> int:
        return len(self._buffer)
    
    def add(self, item: T) -> Optional[List[T]]:
        """
        Add an item to the buffer.
        Returns the buffer content if it should be flushed, else None.
        """
        self._buffer.append(item)
        
        if len(self._buffer) >= self.config.chunk_size:
            return self.flush()
        
        return None
    
    def flush(self) -> List[T]:
        """
        Clear the buffer and return the contents.
        """
        if not self._buffer:
            return []
        
        content = self._buffer
        self._buffer = []
        
        if self.config.enable_gc:
            gc.collect()
            
        logger.debug(f"Flushed buffer of size {len(content)}")
        return content
    
    def is_full(self) -> bool:
        return len(self._buffer) >= self.config.chunk_size

def enforce_memory_limit(max_gb: float = 6.0):
    """
    Context manager or utility to check memory usage (simplified).
    In a real production environment, this would use psutil or similar.
    Here we rely on the chunking logic to enforce limits.
    """
    # Placeholder for actual memory monitoring logic if needed
    # For now, the streaming logic relies on chunk_size to stay within bounds.
    pass

# Export for T022 integration
__all__ = ["StreamingConfig", "StreamingBuffer", "enforce_memory_limit"]
