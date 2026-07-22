"""
CPU-optimized Replay Buffer for DQN training.

Implements a standard Experience Replay buffer with:
- Fixed capacity with FIFO eviction
- Efficient sampling (uniform)
- CPU-only operations (no CUDA tensors stored)
- Memory efficiency via numpy arrays instead of torch tensors

Compatible with src/agents/dqn_agent.py
"""
import numpy as np
import random
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
import logging

from src.utils.config import get_hyperparameter

logger = logging.getLogger(__name__)


@dataclass
class ReplayBufferConfig:
    """Configuration for the replay buffer."""
    capacity: int = 100000
    batch_size: int = 64
    min_buffer_size: int = 1000  # Minimum size before sampling starts
    gamma: float = 0.99  # Discount factor for importance sampling (if used)
    alpha: float = 0.6  # Prioritization exponent (for PER, not used in basic version)
    beta: float = 0.4  # Importance sampling beta (for PER, not used in basic version)
    beta_increment: float = 0.001  # Beta annealing rate

class ReplayBuffer:
    """
    Standard Experience Replay Buffer optimized for CPU training.
    
    Stores transitions (state, action, reward, next_state, done) in circular buffers.
    Uses numpy arrays for memory efficiency and fast sampling.
    """
    
    def __init__(self, config: Optional[ReplayBufferConfig] = None):
        if config is None:
            # Get defaults from config system
            capacity = get_hyperparameter("replay_buffer_capacity", 100000)
            batch_size = get_hyperparameter("replay_buffer_batch_size", 64)
            config = ReplayBufferConfig(capacity=capacity, batch_size=batch_size)
        
        self.config = config
        self.capacity = config.capacity
        self.batch_size = config.batch_size
        self.min_buffer_size = config.min_buffer_size
        
        # Buffer state
        self.position = 0
        self.size = 0
        
        # Pre-allocate numpy arrays for efficiency
        # We use object arrays for state/next_state to handle variable shapes if needed,
        # but typically these will be fixed-size arrays
        self.states = np.empty((capacity, 1), dtype=object)
        self.actions = np.empty(capacity, dtype=np.int64)
        self.rewards = np.empty(capacity, dtype=np.float32)
        self.next_states = np.empty((capacity, 1), dtype=object)
        self.dones = np.empty(capacity, dtype=np.bool_)
        
        # For future priority extensions (currently unused)
        self.priorities = np.ones(capacity, dtype=np.float32)
        
        logger.info(f"Initialized ReplayBuffer with capacity={capacity}, batch_size={batch_size}")
    
    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ) -> None:
        """
        Add a transition to the buffer.
        
        Args:
            state: Current state array
            action: Action taken (integer)
            reward: Reward received (float)
            next_state: Next state array
            done: Whether the episode terminated
        """
        # Store state and next_state as references (they should be copies from the caller)
        self.states[self.position] = state.copy()
        self.actions[self.position] = action
        self.rewards[self.position] = reward
        self.next_states[self.position] = next_state.copy()
        self.dones[self.position] = done
        
        # Circular buffer update
        self.position = (self.position + 1) % self.capacity
        if self.size < self.capacity:
            self.size += 1
    
    def sample(self, batch_size: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Sample a batch of transitions from the buffer.
        
        Args:
            batch_size: Number of samples to draw (defaults to config.batch_size)
        
        Returns:
            Tuple of (states, actions, rewards, next_states, dones) as numpy arrays
        
        Raises:
            ValueError: If buffer size is below min_buffer_size
        """
        if batch_size is None:
            batch_size = self.batch_size
        
        if self.size < self.min_buffer_size:
            raise ValueError(
                f"Cannot sample {batch_size} transitions: buffer size is {self.size} "
                f"(minimum required: {self.min_buffer_size})"
            )
        
        # Sample random indices
        indices = np.random.choice(self.size, size=batch_size, replace=False)
        
        # Extract batches
        states = np.array([self.states[i] for i in indices], dtype=object)
        actions = self.actions[indices]
        rewards = self.rewards[indices]
        next_states = np.array([self.next_states[i] for i in indices], dtype=object)
        dones = self.dones[indices]
        
        return states, actions, rewards, next_states, dones
    
    def sample_with_priorities(
        self, 
        batch_size: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Sample with priority weights (placeholder for PER implementation).
        
        Currently delegates to standard sampling but returns dummy weights.
        
        Returns:
            Tuple of (states, actions, rewards, next_states, dones, indices, weights)
        """
        if batch_size is None:
            batch_size = self.batch_size
        
        states, actions, rewards, next_states, dones = self.sample(batch_size)
        
        # Dummy indices and uniform weights (no prioritization yet)
        indices = np.random.choice(self.size, size=batch_size, replace=False)
        weights = np.ones(batch_size, dtype=np.float32)
        
        return states, actions, rewards, next_states, dones, indices, weights
    
    def __len__(self) -> int:
        """Return current number of transitions in buffer."""
        return self.size
    
    def is_ready(self) -> bool:
        """Check if buffer has enough samples for training."""
        return self.size >= self.min_buffer_size
    
    def clear(self) -> None:
        """Reset the buffer to empty state."""
        self.position = 0
        self.size = 0
        self.priorities[:] = 1.0
        logger.debug("Cleared replay buffer")
    
    def __repr__(self) -> str:
        return f"ReplayBuffer(size={self.size}, capacity={self.capacity})"


def create_replay_buffer(
    config: Optional[ReplayBufferConfig] = None
) -> ReplayBuffer:
    """
    Factory function to create a ReplayBuffer instance.
    
    Args:
        config: Optional configuration. If None, uses defaults or config file.
    
    Returns:
        Initialized ReplayBuffer instance
    """
    return ReplayBuffer(config)
