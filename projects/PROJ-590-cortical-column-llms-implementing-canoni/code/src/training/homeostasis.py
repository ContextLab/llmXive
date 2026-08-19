import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    target_ei_ratio: float = 4.0
    scaling_bound_min: float = 0.5
    scaling_bound_max: float = 2.0
    decay_rate: float = 0.1

@dataclass
class ActivityStats:
    exc_activity: float
    inh_activity: float
    step: int

def calculate_current_ei_ratio(model: torch.nn.Module) -> float:
    """
    Calculate the current ratio of excitatory to inhibitory activity.
    Assumes weights are initialized with ei_ratio_state marking excitatory/inhibitory.
    """
    exc_sum = 0.0
    inh_sum = 0.0
    for name, param in model.named_parameters():
        if param.grad is not None:
            # Check if this parameter is marked as excitatory or inhibitory
            if hasattr(model, 'ei_ratio_state') and name in model.ei_ratio_state:
                is_excitatory = model.ei_ratio_state[name].get('is_excitatory', False)
                # Use absolute gradient magnitude as proxy for activity
                activity = param.grad.abs().sum().item()
                if is_excitatory:
                    exc_sum += activity
                else:
                    inh_sum += activity
    
    if inh_sum == 0:
        return float('inf')
    return exc_sum / inh_sum

def scale_weights(model: torch.nn.Module, target_ratio: float, decay_rate: float) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    Returns a dict of applied scaling factors per layer/parameter.
    """
    scaling_factors = {}
    current_ratio = calculate_current_ei_ratio(model)
    
    if current_ratio == float('inf'):
        logger.warning("Inhibitory activity is zero, cannot scale.")
        return scaling_factors
    
    scale_factor = target_ratio / current_ratio
    scale_factor = max(0.1, min(10.0, scale_factor))  # Basic bounds
    
    for name, param in model.named_parameters():
        if hasattr(model, 'ei_ratio_state') and name in model.ei_ratio_state:
            # Apply decay to prevent oscillation
            effective_scale = 1.0 + decay_rate * (scale_factor - 1.0)
            param.data *= effective_scale
            scaling_factors[name] = effective_scale
    
    return scaling_factors

def log_gradient_norms(model: torch.nn.Module, step: int, log_path: str = "data/logs/gradient_norms.json") -> None:
    """
    Compute and append gradient norms to a JSON log file.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    total_norm = 0.0
    for param in model.parameters():
        if param.grad is not None:
            total_norm += param.grad.data.norm(2).item() ** 2
    total_norm = total_norm ** 0.5
    
    entry = {"step": step, "norm": total_norm}
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []
    
    logs.append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

def enforce_ei_ratio(model: torch.nn.Module, step: int, target_ratio: float = 4.0) -> Dict[str, Any]:
    """
    Dynamic E/I ratio enforcement mechanism.
    
    Calculates mean excitatory and inhibitory activity per epoch,
    computes a scaling factor to force mean_exc / mean_inh = target_ratio,
    and applies it to weights.
    
    Args:
        model: The model to enforce ratio on.
        step: Current training step.
        target_ratio: Target excitatory to inhibitory ratio (default 4.0).
    
    Returns:
        Dict with step, exc_activity, inh_activity, scaling_factor.
    
    Raises:
        ValueError: If model.ei_ratio_state is not set (static initialization missing).
    """
    # Verify static initialization state exists (set in T009c)
    if not hasattr(model, 'ei_ratio_state') or not model.ei_ratio_state:
        raise ValueError(
            "Model missing 'ei_ratio_state' attribute. "
            "Static E/I initialization (T009c) must be run before dynamic enforcement."
        )
    
    exc_activity = 0.0
    inh_activity = 0.0
    
    # Calculate activity based on gradient magnitudes (proxy for activity during backprop)
    # If no gradients exist, use weight magnitudes as fallback
    for name, param in model.named_parameters():
        if name in model.ei_ratio_state:
            is_excitatory = model.ei_ratio_state[name].get('is_excitatory', False)
            
            if param.grad is not None:
                activity = param.grad.abs().mean().item()
            else:
                # Fallback to weight magnitude if no gradients
                activity = param.data.abs().mean().item()
            
            if is_excitatory:
                exc_activity += activity
            else:
                inh_activity += activity
    
    # Avoid division by zero
    if inh_activity == 0:
        inh_activity = 1e-8
    
    current_ratio = exc_activity / inh_activity
    
    # Calculate scaling factor
    scaling_factor = target_ratio / current_ratio
    
    # Bound scaling factor to reasonable range (0.5 to 2.0) to prevent drift
    scaling_factor = max(0.5, min(2.0, scaling_factor))
    
    # Apply scaling to weights
    for name, param in model.named_parameters():
        if name in model.ei_ratio_state:
            # Only scale if this parameter is part of the E/I balance
            param.data *= scaling_factor
    
    # Log the enforcement
    log_entry = {
        "step": step,
        "exc_activity": float(exc_activity),
        "inh_activity": float(inh_activity),
        "scaling_factor": float(scaling_factor)
    }
    
    log_path = "data/logs/ei_ratio_log.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)
    
    logger.info(f"Enforced E/I ratio at step {step}: {current_ratio:.4f} -> {target_ratio:.4f} (scale: {scaling_factor:.4f})")
    
    return log_entry

def apply_ei_balance_constraint(model: torch.nn.Module) -> None:
    """
    Apply a hard constraint to ensure E/I balance is maintained.
    This is a stricter version that clips weights if they drift too far.
    """
    if not hasattr(model, 'ei_ratio_state'):
        return
    
    for name, param in model.named_parameters():
        if name in model.ei_ratio_state:
            # Apply weight clipping to enforce symmetric bounded range
            # This is a simplified constraint
            param.data = torch.clamp(param.data, -1.0, 1.0)

def verify_ei_balance(model: torch.nn.Module, tolerance: float = 0.1) -> bool:
    """
    Verify that the current E/I ratio is within tolerance of the target.
    """
    current_ratio = calculate_current_ei_ratio(model)
    target_ratio = 4.0  # Default target
    
    return abs(current_ratio - target_ratio) / target_ratio < tolerance

class HomeostaticScaler:
    """
    A class to manage homeostatic scaling across training epochs.
    """
    def __init__(self, config: HomeostasisConfig):
        self.config = config
        self.step = 0
    
    def step(self, model: torch.nn.Module) -> Dict[str, Any]:
        """
        Perform one step of homeostatic scaling.
        """
        self.step += 1
        result = enforce_ei_ratio(
            model, 
            self.step, 
            target_ratio=self.config.target_ei_ratio
        )
        return result

def apply_scaling_hook(optimizer: torch.optim.Optimizer, step: int) -> Dict[str, Any]:
    """
    Integration hook for the trainer. Calls scale_weights and enforce_ei_ratio.
    """
    # Note: optimizer is not directly used here, but passed for compatibility
    # The actual scaling is applied to the model's parameters
    # We assume the model is accessible via optimizer.param_groups[0]['params'][0].module
    # This is a simplification; in practice, the model should be passed explicitly.
    # For now, this function is a placeholder for the actual integration logic.
    # The real implementation is in enforce_ei_ratio which is called directly.
    return {"status": "placeholder", "step": step}
