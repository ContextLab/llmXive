import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    target_ei_ratio: float = 4.0
    scaling_decay_rate: float = 0.1
    activity_threshold: float = 0.5
    log_interval: int = 100

@dataclass
class ActivityStats:
    exc_activity: float
    inh_activity: float
    total_activity: float
    exc_count: int
    inh_count: int

def calculate_current_ei_ratio(model: nn.Module) -> Tuple[float, float]:
    """
    Calculate the current excitatory and inhibitory activity ratio in the model.
    Assumes excitatory weights are positive and inhibitory are negative (or separate flags).
    For this implementation, we approximate by summing absolute values of weights
    in layers marked as excitatory vs inhibitory based on naming or config.
    Here, we use a heuristic: weights in layers with 'exc' in name are excitatory,
    'inh' are inhibitory. If no such naming, we default to all excitatory.
    """
    exc_sum = 0.0
    inh_sum = 0.0
    for name, param in model.named_parameters():
        if param.grad is None:
            continue
        if 'exc' in name.lower():
            exc_sum += torch.sum(torch.abs(param.grad)).item()
        elif 'inh' in name.lower():
            inh_sum += torch.sum(torch.abs(param.grad)).item()
        else:
            # Default to excitatory if no label
            exc_sum += torch.sum(torch.abs(param.grad)).item()

    if inh_sum == 0:
        inh_sum = 1e-9  # Avoid division by zero

    return exc_sum, inh_sum

def scale_weights(model: nn.Module, target_ratio: float, decay_rate: float) -> Dict[str, float]:
    """
    Applies synaptic scaling to maintain E/I ratio.
    Formula: scale_factor = target_activity / current_activity
    Returns a dict of applied scaling factors per layer.
    """
    scaling_factors = {}
    current_exc, current_inh = calculate_current_ei_ratio(model)

    if current_inh == 0:
        current_inh = 1e-9

    current_ratio = current_exc / current_inh
    target_activity = target_ratio
    current_activity = current_ratio

    # Calculate global scaling factor to move towards target
    if current_activity == 0:
        scale_factor = 1.0
    else:
        scale_factor = (target_activity / current_activity) ** decay_rate

    for name, param in model.named_parameters():
        if param.grad is not None:
            # Apply scaling to gradients or weights?
            # Typically homeostatic scaling applies to weights to maintain activity
            # Here we scale the weights directly
            param.data *= scale_factor
            scaling_factors[name] = scale_factor

    logger.info(f"Applied scaling factor {scale_factor:.4f} to maintain E/I ratio {target_ratio}")
    return scaling_factors

def log_gradient_norms(model: nn.Module, step: int, log_path: str = "data/logs/gradient_norms.json") -> None:
    """
    Computes and appends gradient norms to a JSON log file.
    """
    norms = []
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = torch.norm(param.grad).item()
            norms.append({"name": name, "norm": norm})

    log_entry = {
        "step": step,
        "timestamp": datetime.utcnow().isoformat(),
        "norms": norms,
        "total_norm": sum(n["norm"] for n in norms)
    }

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(log_entry)

    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Logged gradient norms for step {step} to {log_path}")

def enforce_ei_ratio(model: nn.Module, step: int, target_ratio: float = 4.0, log_path: str = "data/logs/ei_ratio_log.json") -> Dict:
    """
    Dynamically enforces E/I ratio by calculating mean excitatory and inhibitory activity
    and applying scaling factors. Logs the result.
    """
    exc_activity, inh_activity = calculate_current_ei_ratio(model)

    if inh_activity == 0:
        inh_activity = 1e-9

    current_ratio = exc_activity / inh_activity
    scaling_factor = (target_ratio / current_ratio) ** 0.1  # decay rate 0.1

    # Apply scaling to weights
    for param in model.parameters():
        if param.grad is not None:
            param.data *= scaling_factor

    log_entry = {
        "step": step,
        "exc_activity": float(exc_activity),
        "inh_activity": float(inh_activity),
        "current_ratio": float(current_ratio),
        "scaling_factor": float(scaling_factor),
        "timestamp": datetime.utcnow().isoformat()
    }

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(log_entry)

    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Enforced E/I ratio at step {step}: {current_ratio:.4f} -> {target_ratio}, factor={scaling_factor:.4f}")

    return log_entry

def apply_ei_balance_constraint(model: nn.Module) -> None:
    """
    Applies a hard constraint to balance E/I weights if they deviate too much.
    """
    for param in model.parameters():
        if param.grad is not None:
            # Clamp weights to prevent extreme values
            param.data = torch.clamp(param.data, -1.0, 1.0)

def verify_ei_balance(model: nn.Module, target_ratio: float = 4.0, tolerance: float = 0.5) -> bool:
    """
    Verifies if the current E/I ratio is within tolerance of the target.
    """
    exc_activity, inh_activity = calculate_current_ei_ratio(model)
    if inh_activity == 0:
        inh_activity = 1e-9

    current_ratio = exc_activity / inh_activity
    lower_bound = target_ratio - tolerance
    upper_bound = target_ratio + tolerance

    return lower_bound <= current_ratio <= upper_bound

class HomeostaticScaler:
    """
    A class to manage homeostatic scaling over training steps.
    """
    def __init__(self, config: HomeostasisConfig, model: nn.Module):
        self.config = config
        self.model = model
        self.step = 0

    def step(self, optimizer: torch.optim.Optimizer) -> Dict:
        """
        Calls scale_weights and enforce_ei_ratio after each optimizer step.
        Logs factors to data/logs/ei_ratio_log.json and data/logs/gradient_norms.json.
        """
        self.step += 1

        # Log gradient norms
        log_gradient_norms(self.model, self.step)

        # Enforce E/I ratio
        ei_log = enforce_ei_ratio(
            self.model,
            self.step,
            target_ratio=self.config.target_ei_ratio
        )

        # Apply weight scaling
        scaling_factors = scale_weights(
            self.model,
            target_ratio=self.config.target_ei_ratio,
            decay_rate=self.config.scaling_decay_rate
        )

        return {
            "step": self.step,
            "ei_log": ei_log,
            "scaling_factors": scaling_factors
        }

def apply_scaling_hook(optimizer: torch.optim.Optimizer, step: int, model: nn.Module, config: Optional[HomeostasisConfig] = None) -> Dict:
    """
    Integration hook to be called after each optimizer step.
    Calls scale_weights (from T008a) and enforce_ei_ratio (from T008c).
    Logs factors to data/logs/ei_ratio_log.json and data/logs/gradient_norms.json.
    """
    if config is None:
        config = HomeostasisConfig()

    # Log gradient norms
    log_gradient_norms(model, step)

    # Enforce E/I ratio
    ei_log = enforce_ei_ratio(
        model,
        step,
        target_ratio=config.target_ei_ratio
    )

    # Apply weight scaling
    scaling_factors = scale_weights(
        model,
        target_ratio=config.target_ei_ratio,
        decay_rate=config.scaling_decay_rate
    )

    return {
        "step": step,
        "ei_log": ei_log,
        "scaling_factors": scaling_factors
    }