"""
Homeostasis module for implementing homeostatic scaling and gradient logging.
"""
import json
import logging
import os
import fcntl
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Callable
import torch

logger = logging.getLogger(__name__)


@dataclass
class HomeostasisConfig:
    target_activity: float = 1.0
    decay_rate: float = 0.1
    target_ei_ratio: float = 4.0


@dataclass
class ActivityStats:
    current_activity: float
    target_activity: float
    scaling_factor: float


def identify_excitatory_inhibitory_params(
    model: torch.nn.Module
) -> Tuple[List[str], List[str]]:
    """
    Identify excitatory (positive) and inhibitory (negative) parameters.
    For this implementation, we assume all parameters are excitatory by default
    unless explicitly named with 'inhib' in the parameter name.
    """
    excitatory = []
    inhibitory = []

    for name, param in model.named_parameters():
        if 'inhib' in name.lower() or 'inhibitory' in name.lower():
            inhibitory.append(name)
        else:
            excitatory.append(name)

    return excitatory, inhibitory


def calculate_current_activity(model: torch.nn.Module) -> float:
    """
    Calculate the current activity level of the model.
    Uses the L2 norm of all parameters as a proxy for activity.
    """
    total_norm = 0.0
    for param in model.parameters():
        if param.grad is not None:
            total_norm += param.grad.data.norm(2).item() ** 2
    return total_norm ** 0.5


def scale_weights(
    model: torch.nn.Module,
    target_ratio: float,
    decay_rate: float
) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    Formula: scale_factor = target_activity / current_activity
    new_weight = old_weight * (target_activity / current_activity) ** decay_rate

    Args:
        model: The model to scale.
        target_ratio: Target E/I activity ratio.
        decay_rate: Decay rate for the scaling update.

    Returns:
        Dict of applied scaling factors for each parameter.
    """
    applied_factors = {}
    excitatory, inhibitory = identify_excitatory_inhibitory_params(model)

    # Calculate current activities
    exc_activity = 0.0
    inh_activity = 0.0

    for name, param in model.named_parameters():
        if name in excitatory:
            if param.grad is not None:
                exc_activity += param.grad.data.norm(2).item() ** 2
        elif name in inhibitory:
            if param.grad is not None:
                inh_activity += param.grad.data.norm(2).item() ** 2

    exc_activity = exc_activity ** 0.5
    inh_activity = inh_activity ** 0.5 if inh_activity > 0 else 1e-6

    current_ratio = exc_activity / inh_activity

    # Calculate scaling factor to restore target ratio
    scale_factor = (target_ratio / current_ratio) ** decay_rate

    # Apply scaling to excitatory parameters
    for name, param in model.named_parameters():
        if name in excitatory and param.grad is not None:
            with torch.no_grad():
                param.data *= scale_factor
            applied_factors[name] = scale_factor

    logger.info(f"Applied scaling factor {scale_factor:.4f} to {len(excitatory)} excitatory parameters")
    return applied_factors


def enforce_ei_ratio(
    model: torch.nn.Module,
    target_ratio: float = 4.0,
    decay_rate: float = 0.1
) -> Dict[str, float]:
    """
    Enforce E/I ratio constraint via homeostatic scaling.
    """
    return scale_weights(model, target_ratio, decay_rate)


def apply_ei_balance_constraint(
    model: torch.nn.Module,
    target_ratio: float = 4.0,
    decay_rate: float = 0.1
) -> Dict[str, float]:
    """
    Apply E/I balance constraint using homeostatic scaling.
    """
    return enforce_ei_ratio(model, target_ratio, decay_rate)


def verify_ei_balance(
    model: torch.nn.Module,
    target_ratio: float = 4.0,
    tolerance: float = 0.05
) -> bool:
    """
    Verify that the current E/I ratio is within tolerance of the target.
    """
    excitatory, inhibitory = identify_excitatory_inhibitory_params(model)

    exc_activity = 0.0
    inh_activity = 0.0

    for name, param in model.named_parameters():
        if name in excitatory:
            if param.grad is not None:
                exc_activity += param.grad.data.norm(2).item() ** 2
        elif name in inhibitory:
            if param.grad is not None:
                inh_activity += param.grad.data.norm(2).item() ** 2

    exc_activity = exc_activity ** 0.5
    inh_activity = inh_activity ** 0.5 if inh_activity > 0 else 1e-6

    current_ratio = exc_activity / inh_activity
    ratio_diff = abs(current_ratio - target_ratio) / target_ratio

    return ratio_diff <= tolerance


class HomeostaticScaler:
    """
    Homeostatic scaler that applies scaling hooks during training.
    """
    def __init__(
        self,
        model: torch.nn.Module,
        config: HomeostasisConfig
    ):
        self.model = model
        self.config = config
        self.handles: List[Callable] = []

    def register_scaling_hook(self):
        """
        Register a backward hook to apply scaling after each backward pass.
        """
        def hook_fn(module, grad_input, grad_output):
            # Apply scaling after backward
            scale_weights(
                self.model,
                self.config.target_ei_ratio,
                self.config.decay_rate
            )

        for module in self.model.modules():
            handle = module.register_full_backward_hook(hook_fn)
            self.handles.append(handle)

    def cleanup(self):
        """
        Remove all registered hooks.
        """
        for handle in self.handles:
            handle.remove()
        self.handles = []


def apply_scaling_hook(
    model: torch.nn.Module,
    target_ratio: float = 4.0,
    decay_rate: float = 0.1
) -> HomeostaticScaler:
    """
    Apply a scaling hook to the model for homeostatic regulation.
    """
    config = HomeostasisConfig(
        target_activity=1.0,
        decay_rate=decay_rate,
        target_ei_ratio=target_ratio
    )
    scaler = HomeostaticScaler(model, config)
    scaler.register_scaling_hook()
    return scaler


def log_gradient_norms(
    model: torch.nn.Module,
    step: int,
    output_file: str
) -> None:
    """
    Compute and append gradient norms to a specified JSON file.

    This function:
    1. Creates the output file as an empty list if it doesn't exist.
    2. Computes L2 norms for each parameter that has a gradient.
    3. Appends {step: int, norms: {param_name: float}} to the list.
    4. Writes the list back with 2-space indentation and a trailing newline.
    5. Uses file locking for parallel safety.

    Args:
        model: The model whose gradients to log.
        step: The current training step.
        output_file: Path to the JSON file to append to.
    """
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Compute gradient norms
    norms_dict = {}
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = param.grad.data.norm(2).item()
            norms_dict[name] = float(norm)

    entry = {
        "step": step,
        "norms": norms_dict
    }

    # Read existing data, append, and write back with locking
    data: List[Dict[str, Any]] = []

    # Try to read existing file
    if output_path.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                # Use file locking for read
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read existing gradient log: {e}. Starting fresh.")
            data = []

    # Append new entry
    data.append(entry)

    # Write back with locking
    with open(output_file, 'w', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
            f.write('\n')  # Trailing newline
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    logger.debug(f"Logged gradient norms for step {step} to {output_file}")


def verify_independence(
    train_data: torch.Tensor,
    test_data: torch.Tensor
) -> bool:
    """
    Verify that training and test data are from independent distributions.
    Uses Kolmogorov-Smirnov test.

    Args:
        train_data: Training data tensor.
        test_data: Test data tensor.

    Returns:
        True if distributions are statistically distinct (p < 0.05).

    Raises:
        ValueError: If distributions are not distinct (p >= 0.05).
    """
    from scipy import stats

    # Flatten tensors for KS test
    train_flat = train_data.flatten().cpu().numpy()
    test_flat = test_data.flatten().cpu().numpy()

    # Perform KS test
    stat, p_value = stats.ks_2samp(train_flat, test_flat)

    logger.info(f"KS test statistic: {stat:.4f}, p-value: {p_value:.4f}")

    if p_value >= 0.05:
        raise ValueError(
            f"Training and test data distributions are not statistically distinct "
            f"(p={p_value:.4f} >= 0.05). This violates Constitution Principle VII."
        )

    logger.info("Distributions are statistically distinct (p < 0.05)")
    return True


def main():
    """
    Main entry point for testing the homeostasis module.
    """
    logging.basicConfig(level=logging.INFO)

    # Create a simple test model
    class TestModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(10, 5)

        def forward(self, x):
            return self.linear(x)

    model = TestModel()
    x = torch.randn(32, 10)
    y = torch.randn(32, 5)

    # Forward and backward pass
    output = model(x)
    loss = torch.nn.functional.mse_loss(output, y)
    loss.backward()

    # Test gradient logging
    log_gradient_norms(model, step=0, output_file="data/logs/test_gradient_norms.json")

    logger.info("Gradient logging test completed successfully")


if __name__ == "__main__":
    main()
