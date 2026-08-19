import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    target_ei_ratio: float = 4.0
    scaling_decay_rate: float = 0.99
    activity_window: int = 100
    min_scaling_factor: float = 0.1
    max_scaling_factor: float = 10.0

@dataclass
class ActivityStats:
    exc_activity: float = 0.0
    inh_activity: float = 0.0
    total_params: int = 0

def calculate_current_ei_ratio(model: torch.nn.Module) -> Tuple[float, float]:
    """
    Calculate the current excitatory and inhibitory activity from model weights.
    Assumes weights are initialized with E/I distinction (e.g., positive=exc, negative=inh).
    """
    exc_sum = 0.0
    inh_sum = 0.0
    total_params = 0

    for param in model.parameters():
        if param.grad is not None:
            # Use absolute values of weights/gradients to estimate activity
            weights = param.data.abs()
            # Heuristic: separate by sign of mean weight if available, or assume all are mixed
            # For simplicity, we treat positive weights as excitatory and negative as inhibitory
            # This assumes the model has been initialized with sign-based E/I distinction
            mean_weight = param.data.mean()
            if mean_weight >= 0:
                exc_sum += weights.sum().item()
            else:
                inh_sum += weights.sum().item()
            total_params += param.numel()

    if inh_sum == 0:
        inh_sum = 1e-8  # Avoid division by zero

    return exc_sum, inh_sum

def scale_weights(
    model: torch.nn.Module,
    target_ratio: float,
    decay_rate: float = 0.99
) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    Formula: scale_factor = target_activity / current_activity
    Returns a dict of applied scaling factors per layer.
    """
    exc_activity, inh_activity = calculate_current_ei_ratio(model)
    current_ratio = exc_activity / inh_activity if inh_activity > 0 else float('inf')

    # Calculate target activity based on E/I ratio constraint
    # target_exc / target_inh = target_ratio
    # We scale both to move towards target_ratio
    if current_ratio == 0:
        current_ratio = 1e-8

    # Scaling factor to move ratio towards target
    # If current > target, we need to reduce exc or increase inh
    # We apply a global scaling factor to all weights
    if current_ratio > target_ratio:
        # Too much exc, scale down exc or scale up inh
        scale_factor = target_ratio / current_ratio
    else:
        # Too little exc, scale up exc or scale down inh
        scale_factor = target_ratio / current_ratio

    # Apply decay to prevent abrupt changes
    scale_factor = decay_rate * scale_factor + (1 - decay_rate)

    # Clamp to reasonable bounds
    scale_factor = max(0.1, min(10.0, scale_factor))

    scaling_factors = {}
    for name, param in model.named_parameters():
        if param.grad is not None:
            # Apply scaling to weights
            param.data *= scale_factor
            scaling_factors[name] = scale_factor

    logger.info(f"Applied scaling factor: {scale_factor:.4f} (current ratio: {current_ratio:.4f}, target: {target_ratio})")
    return scaling_factors

def log_gradient_norms(
    model: torch.nn.Module,
    step: int,
    log_path: str = "data/logs/gradient_norms.json"
) -> None:
    """
    Compute and append gradient norms to a JSON log file.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    total_norm = 0.0
    for param in model.parameters():
        if param.grad is not None:
            total_norm += param.grad.data.norm(2).item() ** 2
    total_norm = total_norm ** 0.5

    entry = {
        "step": step,
        "total_norm": total_norm
    }

    # Load existing logs
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(entry)

    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

def enforce_ei_ratio(
    model: torch.nn.Module,
    step: int,
    target_ratio: float = 4.0,
    log_path: str = "data/logs/ei_ratio_log.json"
) -> Dict[str, float]:
    """
    Enforce E/I ratio by calculating mean excitatory and inhibitory activity,
    computing a scaling factor, and applying it to weights.
    """
    # Check for static initialization state
    if not hasattr(model, 'ei_ratio_state'):
        raise AttributeError(
            "Model must have 'ei_ratio_state' attribute set during initialization "
            "by T009c before dynamic enforcement can be applied."
        )

    exc_activity, inh_activity = calculate_current_ei_ratio(model)
    current_ratio = exc_activity / inh_activity if inh_activity > 0 else float('inf')

    # Compute scaling factor to force mean_exc / mean_inh = target_ratio
    if current_ratio == 0:
        current_ratio = 1e-8

    scaling_factor = target_ratio / current_ratio

    # Bound scaling factor to reasonable range
    scaling_factor = max(0.1, min(10.0, scaling_factor))

    # Apply scaling to weights
    for param in model.parameters():
        if param.grad is not None:
            param.data *= scaling_factor

    # Log the enforcement
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    entry = {
        "step": step,
        "exc_activity": exc_activity,
        "inh_activity": inh_activity,
        "scaling_factor": scaling_factor
    }

    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(entry)

    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

    logger.info(f"Enforced E/I ratio at step {step}: scaling_factor={scaling_factor:.4f}")
    return {"scaling_factor": scaling_factor}

def apply_ei_balance_constraint(
    model: torch.nn.Module,
    target_ratio: float = 4.0
) -> None:
    """
    Apply a constraint to keep E/I ratio within bounds during training.
    This is a simpler version that just clips weights.
    """
    for param in model.parameters():
        if param.grad is not None:
            # Clip weights to maintain bounded E/I balance
            param.data = torch.clamp(param.data, -1.0, 1.0)

def verify_ei_balance(
    model: torch.nn.Module,
    target_ratio: float = 4.0,
    tolerance: float = 0.5
) -> bool:
    """
    Verify that the current E/I ratio is within tolerance of the target.
    """
    exc_activity, inh_activity = calculate_current_ei_ratio(model)
    current_ratio = exc_activity / inh_activity if inh_activity > 0 else float('inf')

    lower_bound = target_ratio - tolerance
    upper_bound = target_ratio + tolerance

    return lower_bound <= current_ratio <= upper_bound

class HomeostaticScaler:
    """
    A class to manage homeostatic scaling across training steps.
    """
    def __init__(
        self,
        model: torch.nn.Module,
        config: HomeostasisConfig,
        log_dir: str = "data/logs"
    ):
        self.model = model
        self.config = config
        self.log_dir = log_dir
        self.step = 0

    def step(self, optimizer: torch.optim.Optimizer) -> Dict[str, float]:
        """
        Apply scaling hook after each optimizer step.
        Calls scale_weights and enforce_ei_ratio, logs factors.
        """
        self.step += 1

        # Apply synaptic scaling
        scaling_factors = scale_weights(
            self.model,
            target_ratio=self.config.target_ei_ratio,
            decay_rate=self.config.scaling_decay_rate
        )

        # Enforce E/I ratio dynamically
        ei_factors = enforce_ei_ratio(
            self.model,
            step=self.step,
            target_ratio=self.config.target_ei_ratio,
            log_path=os.path.join(self.log_dir, "ei_ratio_log.json")
        )

        # Log gradient norms
        log_gradient_norms(
            self.model,
            step=self.step,
            log_path=os.path.join(self.log_dir, "gradient_norms.json")
        )

        return {**scaling_factors, **ei_factors}

def apply_scaling_hook(
    optimizer: torch.optim.Optimizer,
    step: int,
    model: Optional[torch.nn.Module] = None,
    target_ratio: float = 4.0,
    decay_rate: float = 0.99,
    log_dir: str = "data/logs"
) -> Dict[str, float]:
    """
    Integration hook that calls scale_weights and enforce_ei_ratio after each optimizer step.
    Logs all scaling factors to JSON files.
    """
    if model is None:
        # Try to infer model from optimizer
        if optimizer.param_groups and optimizer.param_groups[0]['params']:
            # Create a dummy model wrapper to access parameters
            # In practice, the trainer should pass the model explicitly
            raise ValueError("Model must be provided to apply_scaling_hook")
        else:
            raise ValueError("Cannot infer model from optimizer")

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # 1. Apply synaptic scaling (T010a)
    scaling_factors = scale_weights(
        model,
        target_ratio=target_ratio,
        decay_rate=decay_rate
    )

    # 2. Enforce E/I ratio dynamically (T010c)
    ei_factors = enforce_ei_ratio(
        model,
        step=step,
        target_ratio=target_ratio,
        log_path=os.path.join(log_dir, "ei_ratio_log.json")
    )

    # 3. Log gradient norms (T010b)
    log_gradient_norms(
        model,
        step=step,
        log_path=os.path.join(log_dir, "gradient_norms.json")
    )

    # Combine and return all factors
    return {**scaling_factors, **ei_factors}