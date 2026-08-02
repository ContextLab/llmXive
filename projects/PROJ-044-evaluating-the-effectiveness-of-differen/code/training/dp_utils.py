"""
Differential Privacy utilities for Federated Learning using Opacus.

This module provides:
- Gaussian noise wrapper configuration for DP-SGD
- Moments accountant setup for privacy budget tracking
- Helper functions to configure Opacus privacy engine
"""

import logging
from typing import Tuple, Optional

import torch
from torch.optim import Optimizer
from torch.nn import Module

from opacus import PrivacyEngine
from opacus.accountants.utils import get_noise_multiplier

logger = logging.getLogger(__name__)


class DPConfig:
    """
    Configuration container for Differential Privacy parameters.

    Attributes:
        noise_multiplier: The noise multiplier (sigma) for Gaussian noise.
            Higher values provide more privacy but less utility.
        max_grad_norm: The maximum norm for gradient clipping.
        target_epsilon: The target privacy budget (epsilon).
        target_delta: The target delta for (epsilon, delta)-DP.
        batch_size: The batch size used for training.
        sample_rate: The fraction of the dataset sampled per batch.
            Calculated as batch_size / total_samples if not provided.
        epochs: Number of training epochs.
    """

    def __init__(
        self,
        noise_multiplier: float = 1.0,
        max_grad_norm: float = 1.0,
        target_epsilon: float = 8.0,
        target_delta: float = 1e-5,
        batch_size: int = 64,
        sample_rate: Optional[float] = None,
        epochs: int = 1,
        num_samples: Optional[int] = None,
    ):
        self.noise_multiplier = noise_multiplier
        self.max_grad_norm = max_grad_norm
        self.target_epsilon = target_epsilon
        self.target_delta = target_delta
        self.batch_size = batch_size
        self.epochs = epochs
        self.num_samples = num_samples

        # Calculate sample rate if not provided and num_samples is available
        if sample_rate is None and num_samples is not None and num_samples > 0:
            self.sample_rate = batch_size / num_samples
        else:
            self.sample_rate = sample_rate

        logger.info(
            f"DPConfig initialized: epsilon={target_epsilon}, "
            f"delta={target_delta}, noise_multiplier={noise_multiplier}, "
            f"max_grad_norm={max_grad_norm}, sample_rate={self.sample_rate}"
        )


def calculate_noise_multiplier(
    epsilon: float,
    delta: float,
    batch_size: int,
    total_samples: int,
    epochs: int,
    max_grad_norm: float = 1.0,
) -> float:
    """
    Calculate the required noise multiplier to achieve a target epsilon.

    Uses the Opacus Moments Accountant to find the noise multiplier.

    Args:
        epsilon: Target privacy budget.
        delta: Target delta.
        batch_size: Training batch size.
        total_samples: Total number of samples in the dataset.
        epochs: Number of training epochs.
        max_grad_norm: Maximum gradient norm for clipping.

    Returns:
        float: The calculated noise multiplier (sigma).
    """
    sample_rate = batch_size / total_samples if total_samples > 0 else 0.0
    steps = int(epochs * total_samples / batch_size)

    if sample_rate <= 0 or steps <= 0:
        logger.warning(
            f"Invalid sample rate ({sample_rate}) or steps ({steps}). "
            "Returning default noise multiplier 1.0."
        )
        return 1.0

    try:
        noise_multiplier = get_noise_multiplier(
            target_epsilon=epsilon,
            target_delta=delta,
            sample_rate=sample_rate,
            steps=steps,
            accountant="moments",
        )
        logger.info(
            f"Calculated noise multiplier: {noise_multiplier:.4f} "
            f"for epsilon={epsilon}, delta={delta}, steps={steps}"
        )
        return noise_multiplier
    except Exception as e:
        logger.error(f"Error calculating noise multiplier: {e}")
        # Fallback to a reasonable default if calculation fails
        return 1.0


def configure_dp_optimizer(
    model: Module,
    optimizer: Optimizer,
    config: DPConfig,
    total_samples: int,
) -> Tuple[Optimizer, PrivacyEngine]:
    """
    Configure the optimizer and attach the PrivacyEngine for DP training.

    This function:
    1. Calculates the noise multiplier if not explicitly set or if target epsilon is provided.
    2. Wraps the optimizer with the PrivacyEngine.
    3. Returns the modified optimizer and the engine.

    Args:
        model: The PyTorch model to train.
        optimizer: The base optimizer (e.g., SGD, Adam).
        config: DPConfig instance with privacy parameters.
        total_samples: Total number of samples in the dataset.

    Returns:
        Tuple[Optimizer, PrivacyEngine]: The DP-enabled optimizer and the privacy engine.
    """
    # Determine noise multiplier
    noise_multiplier = config.noise_multiplier
    if config.target_epsilon > 0 and config.sample_rate is not None:
        # Recalculate based on target epsilon if provided
        steps = int(config.epochs * total_samples / config.batch_size)
        if steps > 0 and config.sample_rate > 0:
            noise_multiplier = get_noise_multiplier(
                target_epsilon=config.target_epsilon,
                target_delta=config.target_delta,
                sample_rate=config.sample_rate,
                steps=steps,
                accountant="moments",
            )
            logger.info(
                f"Updated noise multiplier to {noise_multiplier:.4f} "
                f"to achieve target epsilon {config.target_epsilon}"
            )

    privacy_engine = PrivacyEngine()

    # Attach the privacy engine to the model, optimizer, and dataloader
    # Note: We do not pass dataloader here as it's handled per-client in FedAvg
    # The engine will track the privacy budget as training proceeds.
    optimizer, _, _ = privacy_engine.make_private(
        module=model,
        optimizer=optimizer,
        noise_multiplier=noise_multiplier,
        max_grad_norm=config.max_grad_norm,
    )

    logger.info(
        f"DP Optimizer configured: "
        f"noise_multiplier={noise_multiplier:.4f}, "
        f"max_grad_norm={config.max_grad_norm}"
    )

    return optimizer, privacy_engine


def get_privacy_spent(privacy_engine: PrivacyEngine) -> Tuple[float, float]:
    """
    Retrieve the current privacy budget spent (epsilon, delta).

    Args:
        privacy_engine: The active PrivacyEngine instance.

    Returns:
        Tuple[float, float]: (epsilon, delta) spent so far.
    """
    try:
        epsilon, delta = privacy_engine.get_privacy_spent()
        return epsilon, delta
    except Exception as e:
        logger.warning(f"Could not retrieve privacy spent: {e}")
        return 0.0, 0.0


def validate_dp_config(config: DPConfig, total_samples: int) -> bool:
    """
    Validate the DP configuration for sanity and feasibility.

    Args:
        config: DPConfig instance.
        total_samples: Total number of samples in the dataset.

    Returns:
        bool: True if configuration is valid, False otherwise.
    """
    if config.batch_size <= 0:
        logger.error("Batch size must be positive.")
        return False

    if total_samples <= 0:
        logger.error("Total samples must be positive.")
        return False

    if config.sample_rate is not None and not (0 < config.sample_rate <= 1):
        logger.error(f"Sample rate must be in (0, 1], got {config.sample_rate}")
        return False

    if config.max_grad_norm <= 0:
        logger.error("Max gradient norm must be positive.")
        return False

    if config.target_delta <= 0:
        logger.error("Delta must be positive.")
        return False

    # Check if noise multiplier is reasonable
    if config.noise_multiplier <= 0:
        logger.warning("Noise multiplier is non-positive; training may be unstable.")

    return True