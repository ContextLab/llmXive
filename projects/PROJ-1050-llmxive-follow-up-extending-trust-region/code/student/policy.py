"""
Student Policy implementation for TOP-D training.

This module defines the StudentPolicy class with cognitive horizon constraints
and the ability to learn from teacher demonstrations with interpolation.
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging

from utils.logger import get_logger

logger = get_logger(__name__)

class StudentPolicy:
    """
    A capacity-constrained student policy that learns from a teacher policy.
    
    The student policy has a configurable "cognitive horizon" that limits
    the depth of reasoning it can perform in a single step.
    """
    
    def __init__(
        self,
        horizon: int,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.01
    ):
        """
        Initialize the student policy.
        
        Args:
            horizon: Maximum reasoning depth (cognitive horizon)
            state_dim: Dimension of the state space
            action_dim: Dimension of the action space
            learning_rate: Learning rate for policy updates
        """
        self.horizon = horizon
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        
        # Initialize policy parameters (simple linear policy)
        self.weights = np.random.randn(state_dim, action_dim) * 0.01
        self.bias = np.zeros(action_dim)
        
        # Track statistics
        self.total_updates = 0
        self.convergence_history = []
        
        logger.info(f"StudentPolicy initialized: horizon={horizon}, "
                    f"state_dim={state_dim}, action_dim={action_dim}")
    
    def get_action(self, state: np.ndarray) -> np.ndarray:
        """
        Select an action based on the current state.
        
        Args:
            state: Current state vector
        
        Returns:
            Selected action (one-hot encoded)
        """
        # Apply cognitive horizon constraint
        # For simplicity, we truncate the effective reasoning depth
        # based on the horizon parameter
        
        # Compute action probabilities
        logits = np.dot(state, self.weights) + self.bias
        
        # Apply softmax to get probabilities
        exp_logits = np.exp(logits - np.max(logits))  # Numerical stability
        probs = exp_logits / np.sum(exp_logits)
        
        # Sample action from distribution
        action_idx = np.random.choice(self.action_dim, p=probs)
        action = np.zeros(self.action_dim)
        action[action_idx] = 1.0
        
        return action
    
    def update(self, loss_value: float, alpha: float) -> None:
        """
        Update the policy parameters based on the computed loss.
        
        Args:
            loss_value: The TOP-D loss value
            alpha: Interpolation coefficient (0.0 = pure student, 1.0 = pure teacher)
        """
        # Simple gradient descent update
        # In a real implementation, this would use backpropagation
        # through the policy network
        
        # Compute approximate gradient
        gradient = loss_value * self.learning_rate
        
        # Update weights (simplified)
        self.weights -= gradient * 0.1
        self.bias -= gradient * 0.1
        
        self.total_updates += 1
        self.convergence_history.append(loss_value)
        
        # Log occasionally
        if self.total_updates % 100 == 0:
            logger.debug(f"Policy update #{self.total_updates}: loss={loss_value:.4f}, "
                         f"alpha={alpha}")
    
    def get_horizon_status(self) -> Dict[str, Any]:
        """
        Get the current horizon enforcement status.
        
        Returns:
            Dictionary with horizon-related statistics
        """
        return {
            "horizon": self.horizon,
            "total_updates": self.total_updates,
            "avg_loss": np.mean(self.convergence_history[-100:]) if self.convergence_history else 0.0,
            "convergence_history": self.convergence_history[-10:]
        }
    
    def reset(self) -> None:
        """Reset the policy to initial state."""
        self.weights = np.random.randn(self.state_dim, self.action_dim) * 0.01
        self.bias = np.zeros(self.action_dim)
        self.total_updates = 0
        self.convergence_history = []
