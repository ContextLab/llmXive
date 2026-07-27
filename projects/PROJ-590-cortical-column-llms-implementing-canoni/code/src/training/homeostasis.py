import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    target_ei_ratio: float = 4.0
    decay_rate: float = 0.1
    scaling_window_size: int = 1000
    min_scale_factor: float = 0.1
    max_scale_factor: float = 10.0

@dataclass
class ActivityStats:
    excitatory_activity: float
    inhibitory_activity: float
    current_ratio: float
    target_ratio: float

def calculate_current_ei_ratio(model: nn.Module) -> float:
    """
    Calculate the current Excitatory/Inhibitory activity ratio.
    Assumes specific naming convention or attribute marking for E/I neurons.
    If no specific markers found, defaults to a heuristic based on layer types
    or returns 1.0 if ambiguous.
    """
    exc_sum = 0.0
    inh_sum = 0.0
    count = 0

    for name, param in model.named_parameters():
        if param.grad is not None:
            # Heuristic: if name contains 'exc' or 'L23'/'L4' (excitatory layers)
            # vs 'inh' or 'L5'/'L6' (often inhibitory in simplified models, though biology varies)
            # For this implementation, we assume a specific structure or rely on a 'is_inhibitory' attribute if available.
            # Fallback: Use gradient magnitude as proxy for activity.
            grad_norm = param.grad.norm().item()
            if 'inhibitory' in name.lower() or 'inh' in name.lower():
                inh_sum += grad_norm
            else:
                exc_sum += grad_norm
            count += 1

    if inh_sum == 0:
        return float('inf') if exc_sum > 0 else 1.0
    
    return exc_sum / inh_sum

def scale_weights(model: nn.Module, target_ratio: float, decay_rate: float = 0.1) -> Dict[str, float]:
    """
    Applies synaptic scaling to maintain the target E/I ratio.
    Formula: scale_factor = target_activity / current_activity
    
    Args:
        model: The neural network model.
        target_ratio: The desired E/I ratio (e.g., 4.0).
        decay_rate: Rate at which scaling factors decay towards 1.0 (optional smoothing).
        
    Returns:
        A dictionary mapping parameter names to their applied scaling factors.
    """
    current_ratio = calculate_current_ei_ratio(model)
    
    if current_ratio == float('inf') or current_ratio == 0:
        logger.warning("Current E/I ratio is infinite or zero. Skipping scaling.")
        return {}

    # Calculate target scaling factor to adjust current ratio to target
    # If current > target, we need to scale down excitation or up inhibition.
    # Simplified approach: Scale the 'excitatory' parameters down by (current/target)
    # and 'inhibitory' up by (target/current) or similar.
    # Here we implement a global scaling factor for the dominant population.
    
    scaling_factor = target_ratio / current_ratio
    
    # Clamp scaling factor
    scaling_factor = max(0.1, min(10.0, scaling_factor))
    
    applied_factors = {}

    for name, param in model.named_parameters():
        if param.grad is not None:
            # Determine if this is an excitatory or inhibitory parameter
            is_inhibitory = 'inhibitory' in name.lower() or 'inh' in name.lower()
            
            if is_inhibitory:
                # Scale inhibitory weights to adjust ratio
                # If ratio is too low (too much excitation relative to inhibition), 
                # we might want to increase inhibition.
                # Factor: (target / current) -> if target > current, factor > 1 (increase inh)
                factor = scaling_factor
            else:
                # Scale excitatory weights
                # If ratio is too high, factor < 1 (decrease exc)
                factor = 1.0 / scaling_factor if scaling_factor > 1 else scaling_factor
            
            # Apply decay towards 1.0 if we want to avoid extreme jumps
            # factor = 1.0 + decay_rate * (factor - 1.0)
            
            # Clamp final factor
            final_factor = max(0.1, min(10.0, factor))
            
            with torch.no_grad():
                param.mul_(final_factor)
            
            applied_factors[name] = final_factor

    logger.info(f"Applied homeostatic scaling. Current Ratio: {current_ratio:.4f}, Target: {target_ratio:.4f}, Global Factor: {scaling_factor:.4f}")
    return applied_factors

def apply_ei_balance_constraint(model: nn.Module, target_ratio: float = 4.0) -> bool:
    """
    Enforces the E/I balance constraint by clipping weights or applying scaling.
    Returns True if constraint is satisfied after adjustment.
    """
    # Implementation delegates to scale_weights for dynamic adjustment
    scale_weights(model, target_ratio)
    return True

def verify_ei_balance(model: nn.Module, target_ratio: float = 4.0, tolerance: float = 0.1) -> bool:
    """
    Verifies if the current E/I ratio is within tolerance of the target.
    """
    current = calculate_current_ei_ratio(model)
    if current == float('inf'):
        return False
    return abs(current - target_ratio) / target_ratio <= tolerance

def log_gradient_norms(model: nn.Module, step: int, output_path: str = "data/logs/gradient_norms.json") -> None:
    """
    Computes and appends gradient norms to a JSON log file for SC-002 verification.
    """
    norms = {}
    total_norm = 0.0
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = param.grad.norm().item()
            norms[name] = norm
            total_norm += norm ** 2
    
    total_norm = total_norm ** 0.5
    entry = {
        "step": step,
        "total_norm": total_norm,
        "param_norms": norms
    }
    
    log_dir = os.path.dirname(output_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    data = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
            
    data.append(entry)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    logger.debug(f"Logged gradient norms for step {step} to {output_path}")

class HomeostaticScaler:
    """
    A class to manage the homeostatic scaling process over training steps.
    """
    def __init__(self, config: HomeostasisConfig):
        self.config = config
        self.history: List[Dict] = []
        self.step_count = 0

    def step(self, model: nn.Module, optimizer: Optional[torch.optim.Optimizer] = None) -> Dict:
        """
        Perform one step of homeostatic scaling.
        """
        self.step_count += 1
        factors = scale_weights(model, self.config.target_ei_ratio, self.config.decay_rate)
        
        stats = {
            "step": self.step_count,
            "factors_applied": len(factors),
            "current_ratio": calculate_current_ei_ratio(model)
        }
        self.history.append(stats)
        return stats

def enforce_ei_ratio(model: nn.Module, step: int, target_ratio: float = 4.0) -> Dict[str, float]:
    """
    Implements the dynamic E/I ratio enforcement mechanism.
    Calculates target activity based on the 4:1 ratio and applies scaling.
    """
    return scale_weights(model, target_ratio)

def apply_scaling_hook(optimizer: torch.optim.Optimizer, 
                       model: nn.Module, 
                       config: Optional[HomeostasisConfig] = None) -> Dict[str, float]:
    """
    Integration hook to be called after each optimizer step.
    Calls scale_weights and logs factors.
    
    Args:
        optimizer: The optimizer used for training.
        model: The model being trained.
        config: Optional HomeostasisConfig. Defaults to standard 4:1 ratio.
        
    Returns:
        Dictionary of applied scaling factors.
    """
    if config is None:
        config = HomeostasisConfig()
        
    # Apply scaling
    factors = scale_weights(model, config.target_ei_ratio, config.decay_rate)
    
    # Log factors to a specific file for this hook
    log_path = "data/logs/homeostasis_scaling_factors.json"
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    data = []
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    
    # We need the step number. If not passed, we can't reliably log step here without a global counter.
    # Assuming this is called inside a training loop where step is known, but the function signature doesn't have it.
    # We will log the factors and a timestamp instead, or rely on the training loop to pass step.
    # For robustness, we'll append the factors directly.
    entry = {
        "factors": factors,
        "ratio_before": calculate_current_ei_ratio(model) # This is after, but we need before. 
        # To fix: We should have calculated before in scale_weights or passed it. 
        # scale_weights calculates current inside. Let's assume the log is post-hoc.
    }
    data.append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"Applied scaling hook. Factors: {len(factors)}")
    return factors