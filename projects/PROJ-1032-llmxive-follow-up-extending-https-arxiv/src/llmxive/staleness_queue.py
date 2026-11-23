"""Staleness queue for buffering gradients."""
from typing import List, Optional, Any, Tuple
from collections import deque
import torch
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

class StalenessQueue:
    """Queue to manage gradient staleness in asynchronous RL."""
    
    def __init__(self, buffer_size: int = 10):
        if buffer_size <= 0:
            raise DATA_INTEGRITY_ERROR("Buffer size must be positive")
        self.buffer_size = buffer_size
        self.queue = deque(maxlen=buffer_size)
        self.step_counter = 0
    
    def push(self, gradient: torch.Tensor, staleness: int = 0) -> None:
        """Push a gradient into the queue."""
        self.queue.append({
            "gradient": gradient,
            "staleness": staleness,
            "step": self.step_counter
        })
        self.step_counter += 1
    
    def get_oldest(self) -> Optional[Tuple[torch.Tensor, int]]:
        """Get the oldest gradient and its staleness."""
        if not self.queue:
            return None
        
        oldest = self.queue[0]
        # Clamp staleness to buffer_size - 1
        effective_staleness = min(oldest["staleness"], self.buffer_size - 1)
        return oldest["gradient"], effective_staleness
    
    def pop_oldest(self) -> Optional[Tuple[torch.Tensor, int]]:
        """Pop the oldest gradient from the queue."""
        if not self.queue:
            return None
        
        oldest = self.queue.popleft()
        effective_staleness = min(oldest["staleness"], self.buffer_size - 1)
        return oldest["gradient"], effective_staleness
    
    def __len__(self) -> int:
        return len(self.queue)
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0
