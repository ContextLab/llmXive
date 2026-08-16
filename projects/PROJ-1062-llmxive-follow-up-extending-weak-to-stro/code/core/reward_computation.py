"""
Reward computation module for Direct On-Policy Distillation (Direct-OPD).

This module implements the implicit reward calculation based on the
log-ratio between the student's current policy and the reference policy,
with epsilon-smoothing to ensure numerical stability.

The implicit reward is derived from the KL-divergence approximation:
r(x, y) ≈ log(π_student(y|x) / π_reference(y|x)) + ε

Where ε is a small positive constant to prevent log(0) and ensure
numerical stability during gradient computation.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple

import numpy as np
import torch
from torch import nn

# Default epsilon value for smoothing
DEFAULT_EPSILON = 1e-8
DEFAULT_LOGIT_SCALE = 1.0

logger = logging.getLogger(__name__)


class ImplicitRewardComputer(nn.Module):
    """
    Computes implicit rewards from student and reference model log-probabilities.

    The implicit reward is calculated as the log-ratio of probabilities
    between the student policy and a reference policy, with epsilon-smoothing
    applied to prevent numerical instability.

    Attributes:
        epsilon (float): Small positive constant for numerical stability.
        logit_scale (float): Scaling factor for logits.
    """

    def __init__(
        self,
        epsilon: float = DEFAULT_EPSILON,
        logit_scale: float = DEFAULT_LOGIT_SCALE,
        device: Optional[Union[str, torch.device]] = None
    ):
        """
        Initialize the ImplicitRewardComputer.

        Args:
            epsilon: Small positive constant for smoothing (default: 1e-8).
            logit_scale: Scaling factor for logits (default: 1.0).
            device: Device to place the module on (default: None, uses default device).
        """
        super().__init__()
        self.epsilon = epsilon
        self.logit_scale = logit_scale
        self.device = device or torch.device("cpu")
        
        # Validate epsilon
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be a positive constant, got {epsilon}")
        
        logger.info(f"ImplicitRewardComputer initialized with epsilon={epsilon}, "
                   f"logit_scale={logit_scale}, device={self.device}")

    def forward(
        self,
        student_log_probs: torch.Tensor,
        reference_log_probs: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute implicit rewards from log-probabilities.

        The reward is computed as:
        r = logit_scale * (student_log_probs - reference_log_probs) + epsilon

        Args:
            student_log_probs: Log-probabilities from the student model.
                               Shape: (batch_size, sequence_length) or (batch_size,).
            reference_log_probs: Log-probabilities from the reference model.
                                 Shape: (batch_size, sequence_length) or (batch_size,).
            mask: Optional boolean mask indicating valid tokens.
                  Shape: (batch_size, sequence_length).
                  If None, all tokens are considered valid.

        Returns:
            torch.Tensor: Implicit rewards. Shape matches the input log-probabilities
                          (or reduced to (batch_size,) if per-sample rewards are computed).

        Raises:
            ValueError: If input shapes are incompatible.
            RuntimeError: If computation fails due to numerical issues.
        """
        # Ensure inputs are on the same device
        student_log_probs = student_log_probs.to(self.device)
        reference_log_probs = reference_log_probs.to(self.device)
        
        if mask is not None:
            mask = mask.to(self.device)

        # Validate input shapes
        if student_log_probs.shape != reference_log_probs.shape:
            raise ValueError(
                f"Shape mismatch: student_log_probs {student_log_probs.shape} "
                f"vs reference_log_probs {reference_log_probs.shape}"
            )

        try:
            # Compute log-ratio with epsilon smoothing
            # r = scale * (log_pi_student - log_pi_ref) + epsilon
            log_ratio = student_log_probs - reference_log_probs
            rewards = self.logit_scale * log_ratio + self.epsilon

            # Apply mask if provided
            if mask is not None:
                # Zero out masked positions
                rewards = rewards * mask.to(rewards.dtype)
                
                # Optional: compute mean reward per sample for masked sequences
                # This is useful for policy gradient updates
                mask_sum = mask.sum(dim=-1, keepdim=True).clamp(min=1.0)
                rewards_per_sample = (rewards * mask).sum(dim=-1, keepdim=True) / mask_sum
                rewards = rewards_per_sample.squeeze(-1)

            return rewards

        except Exception as e:
            logger.error(f"Reward computation failed: {e}")
            raise RuntimeError(f"Numerical error during reward computation: {e}") from e

    def compute_per_token_rewards(
        self,
        student_log_probs: torch.Tensor,
        reference_log_probs: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute per-token implicit rewards.

        Similar to forward() but explicitly returns per-token rewards without
        aggregation.

        Args:
            student_log_probs: Log-probabilities from student model.
            reference_log_probs: Log-probabilities from reference model.
            mask: Optional mask for valid tokens.

        Returns:
            torch.Tensor: Per-token rewards with same shape as input.
        """
        return self.forward(student_log_probs, reference_log_probs, mask)

    def compute_sequence_rewards(
        self,
        student_log_probs: torch.Tensor,
        reference_log_probs: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute sequence-level implicit rewards (mean over valid tokens).

        Args:
            student_log_probs: Log-probabilities from student model.
            reference_log_probs: Log-probabilities from reference model.
            mask: Optional mask for valid tokens.

        Returns:
            torch.Tensor: Sequence-level rewards with shape (batch_size,).
        """
        per_token_rewards = self.forward(student_log_probs, reference_log_probs, mask)
        
        # If we already have sequence-level rewards (from forward with mask), return as-is
        if per_token_rewards.dim() == 1:
            return per_token_rewards
        
        # Otherwise, compute mean over valid tokens
        if mask is not None:
            mask_sum = mask.sum(dim=-1, keepdim=True).clamp(min=1.0)
            sequence_rewards = (per_token_rewards * mask).sum(dim=-1) / mask_sum.squeeze(-1)
        else:
            sequence_rewards = per_token_rewards.mean(dim=-1)
        
        return sequence_rewards


def compute_implicit_reward(
    student_log_probs: torch.Tensor,
    reference_log_probs: torch.Tensor,
    epsilon: float = DEFAULT_EPSILON,
    logit_scale: float = DEFAULT_LOGIT_SCALE,
    mask: Optional[torch.Tensor] = None,
    device: Optional[Union[str, torch.device]] = None
) -> torch.Tensor:
    """
    Convenience function to compute implicit reward.

    This is a functional wrapper around ImplicitRewardComputer.

    Args:
        student_log_probs: Log-probabilities from the student model.
        reference_log_probs: Log-probabilities from the reference model.
        epsilon: Smoothing constant (default: 1e-8).
        logit_scale: Scaling factor for logits (default: 1.0).
        mask: Optional mask for valid tokens.
        device: Device to use for computation.

    Returns:
        torch.Tensor: Computed implicit rewards.
    """
    computer = ImplicitRewardComputer(
        epsilon=epsilon,
        logit_scale=logit_scale,
        device=device
    )
    return computer(student_log_probs, reference_log_probs, mask)


def validate_reward_computation(
    student_log_probs: torch.Tensor,
    reference_log_probs: torch.Tensor,
    epsilon: float = DEFAULT_EPSILON,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Validate that reward computation is numerically stable.

    Args:
        student_log_probs: Student log-probabilities to validate.
        reference_log_probs: Reference log-probabilities to validate.
        epsilon: Smoothing constant used.
        tolerance: Acceptable tolerance for numerical checks.

    Returns:
        Dict with validation results:
            - 'valid': bool indicating if computation is valid
            - 'has_nans': bool indicating presence of NaN values
            - 'has_infs': bool indicating presence of Inf values
            - 'min_reward': minimum reward value
            - 'max_reward': maximum reward value
            - 'mean_reward': mean reward value
    """
    computer = ImplicitRewardComputer(epsilon=epsilon)
    
    with torch.no_grad():
        rewards = computer(student_log_probs, reference_log_probs)
    
    has_nans = torch.isnan(rewards).any().item()
    has_infs = torch.isinf(rewards).any().item()
    
    result = {
        'valid': not has_nans and not has_infs,
        'has_nans': has_nans,
        'has_infs': has_infs,
        'min_reward': float(rewards.min()),
        'max_reward': float(rewards.max()),
        'mean_reward': float(rewards.mean()),
        'std_reward': float(rewards.std())
    }
    
    if not result['valid']:
        logger.warning(f"Reward computation validation failed: {result}")
    else:
        logger.info(f"Reward computation validated: min={result['min_reward']:.4f}, "
                   f"max={result['max_reward']:.4f}, mean={result['mean_reward']:.4f}")
    
    return result


def main():
    """
    Main function to demonstrate and test reward computation.
    
    This function creates synthetic test data and runs validation checks
    to ensure the reward computation is working correctly.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set random seed for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)
    
    # Create synthetic test data
    batch_size = 4
    sequence_length = 10
    
    # Generate random log-probabilities (negative values as they are logs)
    student_log_probs = torch.randn(batch_size, sequence_length) * 0.5 - 2.0
    reference_log_probs = torch.randn(batch_size, sequence_length) * 0.5 - 2.0
    
    # Create a mask (some tokens masked)
    mask = torch.ones(batch_size, sequence_length, dtype=torch.bool)
    mask[:, -2:] = False  # Mask last 2 tokens
    
    logger.info("Testing implicit reward computation...")
    logger.info(f"Student log-probs shape: {student_log_probs.shape}")
    logger.info(f"Reference log-probs shape: {reference_log_probs.shape}")
    logger.info(f"Mask shape: {mask.shape}")
    
    # Test basic computation
    rewards = compute_implicit_reward(
        student_log_probs,
        reference_log_probs,
        epsilon=1e-8,
        logit_scale=1.0,
        mask=mask
    )
    
    logger.info(f"Rewards shape: {rewards.shape}")
    logger.info(f"Rewards range: [{rewards.min():.4f}, {rewards.max():.4f}]")
    logger.info(f"Rewards mean: {rewards.mean():.4f}")
    
    # Validate computation
    validation = validate_reward_computation(
        student_log_probs,
        reference_log_probs,
        epsilon=1e-8
    )
    
    logger.info(f"Validation result: {validation}")
    
    if validation['valid']:
        logger.info("✓ Reward computation passed all validation checks")
    else:
        logger.error("✗ Reward computation failed validation")
        raise AssertionError("Reward computation validation failed")
    
    # Test edge cases
    logger.info("\nTesting edge cases...")
    
    # Test with very small epsilon
    rewards_small_eps = compute_implicit_reward(
        student_log_probs,
        reference_log_probs,
        epsilon=1e-12
    )
    logger.info(f"Small epsilon rewards mean: {rewards_small_eps.mean():.4f}")
    
    # Test with large epsilon
    rewards_large_eps = compute_implicit_reward(
        student_log_probs,
        reference_log_probs,
        epsilon=1e-4
    )
    logger.info(f"Large epsilon rewards mean: {rewards_large_eps.mean():.4f}")
    
    # Test with logit scale
    rewards_scaled = compute_implicit_reward(
        student_log_probs,
        reference_log_probs,
        epsilon=1e-8,
        logit_scale=2.0
    )
    logger.info(f"Scaled rewards mean: {rewards_scaled.mean():.4f}")
    
    logger.info("\n✓ All reward computation tests completed successfully")


if __name__ == "__main__":
    main()