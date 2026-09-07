"""
TOP-D (Trust Region Policy Distillation) Loss implementation.

This module implements the loss function that interpolates between
student and teacher policies using the alpha coefficient.
"""
import numpy as np
from typing import Union, Optional, Dict, Any
import logging

from utils.logger import get_logger

logger = get_logger(__name__)

class TOPDLoss:
    """
    TOP-D Loss function for policy distillation.
    
    The loss is computed as an interpolation between:
    - Student's own loss (when alpha = 0)
    - Teacher's guidance (when alpha = 1)
    """
    
    def __init__(
        self,
        temperature: float = 1.0,
        kl_weight: float = 0.5
    ):
        """
        Initialize the TOP-D loss function.
        
        Args:
            temperature: Temperature for softmax (higher = softer probabilities)
            kl_weight: Weight for KL divergence term
        """
        self.temperature = temperature
        self.kl_weight = kl_weight
        logger.debug(f"TOPDLoss initialized: temperature={temperature}, "
                     f"kl_weight={kl_weight}")
    
    def compute_loss(
        self,
        state: np.ndarray,
        teacher_action: np.ndarray,
        student_action: np.ndarray,
        alpha: float
    ) -> float:
        """
        Compute the TOP-D loss for a single state-action pair.
        
        Args:
            state: Current state vector
            teacher_action: Teacher's optimal action (one-hot)
            student_action: Student's selected action (one-hot)
            alpha: Interpolation coefficient (0.0 to 1.0)
        
        Returns:
            Computed loss value
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"Alpha must be between 0.0 and 1.0, got {alpha}")
        
        # Compute student's probability distribution
        # (In a real implementation, this would come from the policy network)
        student_logits = np.dot(state, np.random.randn(state.shape[0], teacher_action.shape[0]))
        student_probs = self._softmax(student_logits / self.temperature)
        
        # Compute teacher's probability distribution (one-hot for optimal action)
        teacher_probs = teacher_action.copy()
        
        # Compute cross-entropy loss
        student_loss = -np.sum(teacher_probs * np.log(student_probs + 1e-8))
        
        # Compute KL divergence between student and teacher
        kl_div = np.sum(teacher_probs * np.log(teacher_probs / (student_probs + 1e-8)))
        
        # Interpolate based on alpha
        # alpha = 0: Pure student learning (minimize student_loss)
        # alpha = 1: Pure teacher distillation (minimize KL divergence)
        loss = (1 - alpha) * student_loss + alpha * (self.kl_weight * kl_div)
        
        return float(loss)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax with numerical stability."""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
    
    def get_loss_components(
        self,
        state: np.ndarray,
        teacher_action: np.ndarray,
        student_action: np.ndarray,
        alpha: float
    ) -> Dict[str, float]:
        """
        Get individual components of the TOP-D loss.
        
        Args:
            state: Current state vector
            teacher_action: Teacher's optimal action
            student_action: Student's selected action
            alpha: Interpolation coefficient
        
        Returns:
            Dictionary with loss components
        """
        student_logits = np.dot(state, np.random.randn(state.shape[0], teacher_action.shape[0]))
        student_probs = self._softmax(student_logits / self.temperature)
        teacher_probs = teacher_action.copy()
        
        student_loss = -np.sum(teacher_probs * np.log(student_probs + 1e-8))
        kl_div = np.sum(teacher_probs * np.log(teacher_probs / (student_probs + 1e-8)))
        
        return {
            "student_loss": float(student_loss),
            "kl_divergence": float(kl_div),
            "interpolated_loss": float((1 - alpha) * student_loss + alpha * self.kl_weight * kl_div)
        }
