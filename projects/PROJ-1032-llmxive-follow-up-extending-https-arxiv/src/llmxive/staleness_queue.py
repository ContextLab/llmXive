"""Staleness queue for buffering gradients in asynchronous RL."""
from typing import List, Optional, Any, Deque
from collections import deque
import torch

class StalenessQueue:
    """
    A queue that manages gradient updates with a configurable staleness delay.
    
    Attributes:
        buffer_size: Maximum number of items the queue can hold.
        staleness: The delay in steps before an update is applied.
    """
    def __init__(self, buffer_size: int, staleness: int):
        """
        Initialize the StalenessQueue.
        
        Args:
            buffer_size: Maximum capacity of the queue.
            staleness: Number of steps to delay updates.
        """
        self.buffer_size = buffer_size
        self.staleness = staleness
        self._queue: Deque[torch.Tensor] = deque(maxlen=buffer_size)
        self._current_step = 0

    def push(self, gradient: torch.Tensor) -> Optional[torch.Tensor]:
        """
        Push a gradient into the queue.
        
        If the staleness threshold is met, returns the gradient to be applied.
        Otherwise, returns None.
        
        Args:
            gradient: The gradient tensor to store.
        
        Returns:
            The gradient to apply (if staleness met), else None.
        """
        # Clamp staleness to buffer_size - 1 if exceeded (Edge Case)
        effective_staleness = min(self.staleness, self.buffer_size - 1)
        
        self._queue.append(gradient)
        
        if len(self._queue) > effective_staleness:
            # Pop the oldest gradient that is now stale enough
            return self._queue.popleft()
        
        return None

    def get_pending(self) -> List[torch.Tensor]:
        """Return all pending gradients in the queue."""
        return list(self._queue)

    def clear(self):
        """Clear the queue."""
        self._queue.clear()
        self._current_step = 0
