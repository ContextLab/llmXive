"""
StalenessQueue: A buffer for managing asynchronous gradient updates with staleness tracking.

This module implements a queue-based mechanism to store gradients and their associated
staleness values. It ensures that stale gradients (exceeding buffer size) are clamped
to the maximum allowable staleness to prevent memory leaks and maintain stability.

Dependencies:
  - torch: For tensor operations
  - collections.deque: For efficient queue operations
  - typing: For type hints
"""

from typing import List, Optional, Any, Tuple
from collections import deque
import torch

from src.llmxive.exceptions import DATA_INTEGRITY_ERROR


class StalenessQueue:
    """
    A queue that buffers gradients and tracks their staleness.
    
    In asynchronous RL training, gradients computed at step `t` might be applied
    at step `t + k`. The `k` is the staleness. This queue manages a buffer of
    such gradients, ensuring that if the staleness exceeds the buffer capacity,
    the value is clamped to `buffer_size - 1` as per the edge case requirement.
    
    Attributes:
        buffer_size (int): Maximum number of items the queue can hold.
        queue (deque): Internal deque storing tuples of (staleness, gradient).
    """
    
    def __init__(self, buffer_size: int):
        """
        Initialize the StalenessQueue.
        
        Args:
            buffer_size (int): The maximum number of gradient steps to buffer.
                               Must be a positive integer.
        
        Raises:
            DATA_INTEGRITY_ERROR: If buffer_size is not positive.
        """
        if buffer_size <= 0:
            raise DATA_INTEGRITY_ERROR(f"buffer_size must be positive, got {buffer_size}")
        
        self.buffer_size = buffer_size
        self.queue: deque = deque(maxlen=buffer_size)
    
    def push(self, staleness: int, gradient: torch.Tensor) -> None:
        """
        Push a gradient with its associated staleness into the queue.
        
        If the provided staleness exceeds `buffer_size - 1`, it is clamped to
        `buffer_size - 1` to satisfy the edge case requirement.
        
        Args:
            staleness (int): The staleness value for this gradient.
            gradient (torch.Tensor): The gradient tensor to store.
        
        Raises:
            DATA_INTEGRITY_ERROR: If gradient is None or not a torch.Tensor.
        """
        if gradient is None or not isinstance(gradient, torch.Tensor):
            raise DATA_INTEGRITY_ERROR("Gradient must be a valid torch.Tensor")
        
        # Clamp staleness to buffer_size - 1 if exceeded (Edge Case Requirement)
        if staleness >= self.buffer_size:
            staleness = self.buffer_size - 1
        
        # Detach gradient to avoid tracking history if needed, but keep data
        # We store the tensor as is, assuming caller manages memory
        self.queue.append((staleness, gradient.detach().clone()))
    
    def pop(self) -> Optional[Tuple[int, torch.Tensor]]:
        """
        Remove and return the oldest (FIFO) gradient and its staleness.
        
        Returns:
            Optional[Tuple[int, torch.Tensor]]: A tuple of (staleness, gradient)
            if the queue is not empty, None otherwise.
        """
        if len(self.queue) == 0:
            return None
        
        return self.queue.popleft()
    
    def peek(self) -> Optional[Tuple[int, torch.Tensor]]:
        """
        View the oldest gradient without removing it.
        
        Returns:
            Optional[Tuple[int, torch.Tensor]]: The oldest (staleness, gradient) tuple,
            or None if the queue is empty.
        """
        if len(self.queue) == 0:
            return None
        
        return self.queue[0]
    
    def get_all(self) -> List[Tuple[int, torch.Tensor]]:
        """
        Return a list of all (staleness, gradient) pairs in the queue.
        
        Returns:
            List[Tuple[int, torch.Tensor]]: A list of tuples from oldest to newest.
        """
        return list(self.queue)
    
    def __len__(self) -> int:
        """Return the current number of items in the queue."""
        return len(self.queue)
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self.queue) == 0
    
    def is_full(self) -> bool:
        """Check if the queue has reached its buffer size."""
        return len(self.queue) >= self.buffer_size
