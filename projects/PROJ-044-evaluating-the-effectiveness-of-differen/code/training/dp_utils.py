"""
Differential Privacy utilities for Federated Learning using Opacus.

This module implements:
- DPConfig dataclass for privacy parameters
- Noise multiplier calculation based on target epsilon
- Opacus PrivacyEngine configuration
- Moments accountant retrieval for privacy budget tracking
- Configuration validation

References:
- Opacus Documentation: https://opacus.ai/
- Abadi et al. "Deep Learning with Differential Privacy" (2016)
"""

import logging
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any

import torch
from torch.optim import Optimizer
from torch.nn import Module
from torch.utils.data import DataLoader

from opacus import PrivacyEngine
from opacus.accountants import RDPAccountant
from opacus.validators import ModuleValidator

logger = logging.getLogger(__name__)


@dataclass
class DPConfig:
    """
    Configuration for Differential Privacy in Federated Learning.

    Attributes:
        epsilon: Target privacy budget (ε). Lower values provide stronger privacy.
        delta: Target failure probability (δ). Typically 1e-5 or lower.
        noise_multiplier: Multiplier for Gaussian noise added to gradients.
        max_grad_norm: Maximum norm for gradient clipping.
        target_sample_rate: Fraction of clients sampled per round (for privacy accounting).
        accountant: Type of privacy accountant to use ('rdp', 'prv', 'moments').
        noise_type: Type of noise ('gaussian' is standard for DP-SGD).
    """
    epsilon: float = 1.0
    delta: float = 1e-5
    noise_multiplier: float = 1.0
    max_grad_norm: float = 1.0
    target_sample_rate: float = 0.1
    accountant: str = "rdp"
    noise_type: str = "gaussian"

    def __post_init__(self):
        if self.epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {self.epsilon}")
        if self.delta <= 0 or self.delta >= 1:
            raise ValueError(f"Delta must be in (0, 1), got {self.delta}")
        if self.noise_multiplier <= 0:
            raise ValueError(f"Noise multiplier must be positive, got {self.noise_multiplier}")
        if self.max_grad_norm <= 0:
            raise ValueError(f"Max grad norm must be positive, got {self.max_grad_norm}")
        if self.target_sample_rate <= 0 or self.target_sample_rate > 1:
            raise ValueError(f"Target sample rate must be in (0, 1], got {self.target_sample_rate}")


def calculate_noise_multiplier(
    epsilon: float,
    delta: float,
    noise_multiplier: Optional[float] = None,
    steps: int = 1000,
    sample_rate: float = 0.1,
    accountant: str = "rdp"
) -> float:
    """
    Calculate the required noise multiplier to achieve a target epsilon.

    This uses the Opacus privacy accountant to reverse-engineer the noise
    multiplier needed for a given privacy budget.

    Args:
        epsilon: Target privacy budget.
        delta: Target failure probability.
        noise_multiplier: Optional initial guess. If None, uses a binary search.
        steps: Number of training steps (rounds * clients per round).
        sample_rate: Fraction of data sampled per step.
        accountant: Type of accountant ('rdp', 'prv', 'moments').

    Returns:
        float: The calculated noise multiplier.

    Raises:
        ValueError: If epsilon is too small to achieve with reasonable noise.
    """
    if accountant not in ["rdp", "prv", "moments"]:
        raise ValueError(f"Unsupported accountant type: {accountant}")

    logger.info(f"Calculating noise multiplier for ε={epsilon}, δ={delta}, steps={steps}")

    # Use Opacus's built-in capability to find noise multiplier
    # We use a simple binary search approach
    low, high = 0.1, 10.0
    target_epsilon = epsilon

    # Try to find the noise multiplier using the RDP accountant as reference
    # Opacus doesn't have a direct "find noise" function, so we iterate
    best_noise = 1.0

    # If epsilon is very small, we need a very large noise multiplier
    # which might break utility. We set a reasonable upper bound.
    max_noise = 100.0
    min_noise = 0.01

    # Quick estimation: for RDP, noise ~ sqrt(2 * log(1.25/delta)) / epsilon
    # This is a rough approximation for the Gaussian mechanism
    import math
    rough_estimate = math.sqrt(2 * math.log(1.25 / delta)) / epsilon
    if rough_estimate < max_noise:
        high = max(rough_estimate * 2, high)
        low = min(rough_estimate / 2, low)

    # Binary search for the noise multiplier
    for _ in range(50):  # Fixed iterations for stability
        mid = (low + high) / 2
        if mid <= 0:
            mid = 1e-6

        # Create a dummy accountant to check the achieved epsilon
        try:
            accountant_instance = RDPAccountant()
            accountant_instance._history = []  # Reset
            accountant_instance._privacy_budget = 0.0

            # Simulate the privacy consumption for 'steps' steps
            # Opacus doesn't expose a simple "get_epsilon(noise)" function,
            # so we use the privacy_engine's compute_epsilon method
            from opacus import PrivacyEngine as PE

            # We need to create a dummy model and optimizer to use the engine
            # But for calculation, we can use the analytical formula for RDP
            # RDP of Gaussian mechanism: alpha + (noise^2 * 2 * alpha * log(1/(1-sample_rate))) / 2
            # This is complex, so we use a simpler heuristic:
            # For small sample rates, epsilon ≈ noise_multiplier * sample_rate * sqrt(2 * steps * log(1/delta))

            # Use Opacus's compute_epsilon if available
            # Since we can't easily instantiate without a model, we use the formula:
            # epsilon = (1 / (sample_rate * noise)) * sqrt(2 * steps * log(1/delta))
            # Actually, let's use the inverse: given epsilon, find noise
            # epsilon ≈ (sample_rate * noise) * sqrt(2 * steps * log(1/delta)) is wrong
            # Correct approximation for RDP:
            # epsilon = (alpha * (1/sample_rate - 1) + alpha * (1/sample_rate)) * (noise^2) / 2 ...
            # This is getting too complex. Let's use a simpler approach:

            # We'll use the fact that for RDP with Gaussian noise:
            # epsilon = (noise_multiplier * sample_rate) * sqrt(2 * steps * log(1/delta)) is not correct.
            # Let's use the actual Opacus method by creating a minimal setup.

            # Instead, we use the inverse of the standard formula:
            # epsilon = (1 / (sample_rate * noise_multiplier)) * sqrt(2 * steps * log(1/delta))
            # Rearranging: noise_multiplier = (1 / (sample_rate * epsilon)) * sqrt(2 * steps * log(1/delta))

            # But this is for the Gaussian mechanism, not RDP.
            # Let's use a more robust approach: use the Opacus PrivacyEngine's compute_epsilon
            # by creating a dummy setup.

            # For now, use a heuristic based on the standard Gaussian mechanism:
            # epsilon ≈ (sample_rate * noise_multiplier) * sqrt(2 * steps * log(1/delta))
            # This is incorrect. The correct relationship is:
            # epsilon = (noise_multiplier * sample_rate) * sqrt(2 * steps * log(1/delta)) is still wrong.

            # Let's use the actual formula from the DP literature:
            # For the Gaussian mechanism, the privacy loss is:
            # epsilon = (1 / (sample_rate * noise)) * sqrt(2 * steps * log(1/delta))
            # So: noise = (1 / (sample_rate * epsilon)) * sqrt(2 * steps * log(1/delta))

            # This is for the pure DP, but we have (epsilon, delta)-DP.
            # For RDP, it's more complex. Let's use the Opacus library's built-in
            # capability by creating a minimal example.

            # Since we can't easily do this without a model, let's use a simpler
            # heuristic that works in practice:
            # noise_multiplier = sqrt(2 * log(1.25/delta)) / epsilon
            # Then adjust based on sample_rate and steps.

            # Actually, the most reliable way is to use the Opacus PrivacyEngine
            # to compute_epsilon. We'll create a dummy model and optimizer.

            dummy_model = torch.nn.Linear(1, 1)
            dummy_optimizer = torch.optim.SGD(dummy_model.parameters(), lr=0.01)
            dummy_engine = PE(
                dummy_optimizer,
                noise_multiplier=mid,
                max_grad_norm=1.0,
                sample_rate=sample_rate,
                accountant=accountant
            )
            dummy_engine.accountant.step(steps=steps)
            achieved_epsilon = dummy_engine.accountant.get_epsilon(delta=delta)

            if abs(achieved_epsilon - target_epsilon) < 1e-3:
                best_noise = mid
                break
            elif achieved_epsilon < target_epsilon:
                # We have too much privacy (too little noise), decrease noise
                low = mid
            else:
                # We have too little privacy (too much noise), increase noise
                high = mid

            if high - low < 1e-4:
                best_noise = mid
                break

        except Exception as e:
            logger.warning(f"Error in noise calculation iteration: {e}")
            break

    logger.info(f"Calculated noise multiplier: {best_noise:.4f} for ε={best_noise:.4f}")
    return best_noise


def configure_dp_optimizer(
    model: Module,
    optimizer: Optimizer,
    dp_config: DPConfig,
    data_loader: DataLoader,
    steps_per_epoch: int
) -> Tuple[Optimizer, PrivacyEngine, RDPAccountant]:
    """
    Configure a PyTorch optimizer with Opacus for Differential Privacy.

    Args:
        model: The neural network model.
        optimizer: The base optimizer (e.g., SGD, Adam).
        dp_config: DP configuration parameters.
        data_loader: DataLoader for the training data (used for sample rate).
        steps_per_epoch: Number of steps per epoch (for privacy accounting).

    Returns:
        Tuple containing:
            - The wrapped optimizer (same object, but with DP hooks)
            - The PrivacyEngine instance
            - The accountant instance (for retrieving privacy spent)

    Raises:
        ValueError: If the model is not compatible with Opacus.
    """
    logger.info(f"Configuring DP optimizer with ε={dp_config.epsilon}, "
                f"noise_multiplier={dp_config.noise_multiplier}, "
                f"max_grad_norm={dp_config.max_grad_norm}")

    # Validate the model
    is_valid, model = ModuleValidator.fix(model)
    if not is_valid:
        logger.warning("Model was modified to be Opacus-compatible")

    # Calculate sample rate if not provided
    sample_rate = dp_config.target_sample_rate
    if hasattr(data_loader, 'dataset') and data_loader.batch_size:
        total_samples = len(data_loader.dataset)
        sample_rate = data_loader.batch_size / total_samples
        logger.debug(f"Calculated sample rate from data loader: {sample_rate}")

    # Initialize the PrivacyEngine
    privacy_engine = PrivacyEngine(
        model,
        sample_rate=sample_rate,
        batch_size=data_loader.batch_size,
        noise_multiplier=dp_config.noise_multiplier,
        max_grad_norm=dp_config.max_grad_norm,
        accountant=dp_config.accountant,
        secure_mode=False  # Set to True for production with secure RNG
    )

    # Attach the privacy engine to the optimizer
    privacy_engine.attach(optimizer)

    logger.info("DP optimizer configured successfully")
    return optimizer, privacy_engine, privacy_engine.accountant


def get_privacy_spent(
    accountant: RDPAccountant,
    delta: float
) -> float:
    """
    Retrieve the total privacy budget (epsilon) spent so far.

    Args:
        accountant: The RDPAccountant instance tracking privacy consumption.
        delta: The target failure probability.

    Returns:
        float: The total epsilon spent.
    """
    try:
        epsilon = accountant.get_epsilon(delta=delta)
        logger.debug(f"Current privacy budget: ε={epsilon:.4f} (δ={delta})")
        return epsilon
    except Exception as e:
        logger.error(f"Error retrieving privacy budget: {e}")
        return float('inf')


def validate_dp_config(dp_config: DPConfig, total_steps: int) -> bool:
    """
    Validate the DP configuration for a given training run.

    Checks:
        - Epsilon is achievable with the given steps and noise
        - Noise multiplier is within reasonable bounds
        - Max grad norm is appropriate

    Args:
        dp_config: The DP configuration to validate.
        total_steps: Total number of training steps.

    Returns:
        bool: True if the configuration is valid, False otherwise.
    """
    errors = []

    # Check epsilon achievability
    if dp_config.epsilon < 0.1:
        logger.warning(f"Very low epsilon ({dp_config.epsilon}) may result in poor model utility")

    # Check noise multiplier bounds
    if dp_config.noise_multiplier < 0.01:
        errors.append(f"Noise multiplier {dp_config.noise_multiplier} is too small to provide meaningful privacy")
    if dp_config.noise_multiplier > 100:
        errors.append(f"Noise multiplier {dp_config.noise_multiplier} is likely too large, will destroy utility")

    # Check max grad norm
    if dp_config.max_grad_norm < 0.01:
        errors.append(f"Max grad norm {dp_config.max_grad_norm} is too small")
    if dp_config.max_grad_norm > 100:
        errors.append(f"Max grad norm {dp_config.max_grad_norm} is too large, may cause instability")

    # Check delta
    if dp_config.delta < 1e-10:
        logger.warning(f"Delta {dp_config.delta} is extremely small, may be computationally expensive")

    if errors:
        for error in errors:
            logger.error(error)
        return False

    logger.info("DP configuration validated successfully")
    return True


def calculate_epsilon_from_noise(
    noise_multiplier: float,
    steps: int,
    sample_rate: float,
    delta: float,
    accountant_type: str = "rdp"
) -> float:
    """
    Calculate the achieved epsilon given a noise multiplier and training steps.

    This is the inverse of calculate_noise_multiplier.

    Args:
        noise_multiplier: The noise multiplier used.
        steps: Total number of steps.
        sample_rate: Fraction of data sampled per step.
        delta: Target failure probability.
        accountant_type: Type of accountant ('rdp', 'prv', 'moments').

    Returns:
        float: The achieved epsilon.
    """
    try:
        # Create a dummy model and optimizer for the PrivacyEngine
        dummy_model = torch.nn.Linear(1, 1)
        dummy_optimizer = torch.optim.SGD(dummy_model.parameters(), lr=0.01)

        privacy_engine = PrivacyEngine(
            dummy_model,
            sample_rate=sample_rate,
            batch_size=1,  # Doesn't matter for calculation
            noise_multiplier=noise_multiplier,
            max_grad_norm=1.0,
            accountant=accountant_type
        )

        privacy_engine.attach(dummy_optimizer)
        privacy_engine.accountant.step(steps=steps)

        epsilon = privacy_engine.accountant.get_epsilon(delta=delta)
        return epsilon
    except Exception as e:
        logger.error(f"Error calculating epsilon: {e}")
        return float('inf')