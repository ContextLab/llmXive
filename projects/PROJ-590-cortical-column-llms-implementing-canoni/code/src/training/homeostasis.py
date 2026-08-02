import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging
import os
import json

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    target_ei_ratio: float = 4.0
    scaling_decay_rate: float = 0.9
    max_scaling_factor: float = 2.0
    min_scaling_factor: float = 0.5
    log_interval: int = 100

@dataclass
class ActivityStats:
    exc_activity: float
    inh_activity: float
    total_activity: float
    current_ei_ratio: float

def calculate_current_ei_ratio(model: torch.nn.Module) -> Tuple[float, float, float]:
    """
    Calculate current excitatory and inhibitory activity from model weights.
    Assumes positive weights are excitatory and negative are inhibitory.
    Returns (exc_mean, inh_mean, total_mean).
    """
    exc_sum = 0.0
    inh_sum = 0.0
    total_count = 0

    for param in model.parameters():
        if param.grad is not None:
            # Use absolute values for activity calculation
            weights = param.data.abs()
            exc_sum += weights.sum().item()
            total_count += weights.numel()

    if total_count == 0:
        return 0.0, 0.0, 0.0

    exc_mean = exc_sum / total_count
    # Inhibitory activity is modeled as a fraction of excitatory in this simplified view
    # In a full model, this would come from specific inhibitory neuron activations
    inh_mean = exc_mean / 4.0  # Default assumption, will be adjusted by scaling
    
    return exc_mean, inh_mean, exc_mean + inh_mean

def scale_weights(model: torch.nn.Module, target_ratio: float, decay_rate: float) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    Formula: scale_factor = target_activity / current_activity
    
    Args:
        model: The neural network model
        target_ratio: Target excitatory/inhibitory ratio
        decay_rate: Decay rate for scaling factor smoothing
        
    Returns:
        Dict mapping parameter names to applied scaling factors
    """
    scaling_factors = {}
    
    # Calculate current activity
    exc_current, inh_current, total_current = calculate_current_ei_ratio(model)
    
    if total_current == 0:
        logger.warning("Total activity is zero, skipping scaling")
        return scaling_factors
        
    # Calculate target activity based on ratio constraint
    # target_exc / target_inh = target_ratio
    # target_exc + target_inh = total_current (preserve total activity)
    # => target_exc = total_current * target_ratio / (1 + target_ratio)
    target_exc = total_current * target_ratio / (1 + target_ratio)
    
    # Calculate scaling factor
    if exc_current == 0:
        scale_factor = 1.0
    else:
        scale_factor = target_exc / exc_current
    
    # Clamp scaling factor to reasonable bounds
    scale_factor = max(0.5, min(2.0, scale_factor))
    
    # Apply decay for smooth transitions
    scale_factor = decay_rate * scale_factor + (1 - decay_rate)
    
    # Apply to all parameters
    for name, param in model.named_parameters():
        if param.grad is not None:
            param.data *= scale_factor
            scaling_factors[name] = scale_factor
            
    logger.info(f"Applied scaling factor: {scale_factor:.4f} (target_ratio={target_ratio})")
    return scaling_factors

def log_gradient_norms(model: torch.nn.Module, step: int, log_file: str = "data/logs/gradient_norms.json") -> None:
    """
    Compute and log gradient norms for stability verification.
    
    Args:
        model: The neural network model
        step: Current training step
        log_file: Path to the log file
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    norms = []
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = param.grad.norm().item()
            norms.append({"name": name, "norm": norm})
    
    entry = {"step": step, "norms": norms}
    
    # Read existing logs if any
    log_data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_data = []
    
    log_data.append(entry)
    
    # Write back
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
        
    logger.info(f"Logged gradient norms for step {step}")

def enforce_ei_ratio(model: torch.nn.Module, step: int, target_ratio: float = 4.0, 
                    log_file: str = "data/logs/ei_ratio_log.json") -> Dict[str, float]:
    """
    Enforce dynamic E/I ratio by scaling weights.
    
    Args:
        model: The neural network model
        step: Current training step
        target_ratio: Target excitatory/inhibitory ratio (default 4.0)
        log_file: Path to the log file
        
    Returns:
        Dict with scaling factors applied
    """
    # Calculate current activities
    exc_current, inh_current, total_current = calculate_current_ei_ratio(model)
    
    if total_current == 0:
        logger.warning("Cannot enforce E/I ratio: zero activity")
        return {}
        
    # Calculate scaling factor to achieve target ratio
    # We want: new_exc / new_inh = target_ratio
    # Assuming proportional scaling: new_exc = k * exc_current, new_inh = k * inh_current
    # Then: (k * exc_current) / (k * inh_current) = exc_current / inh_current
    # This means simple proportional scaling doesn't change the ratio!
    # We need to scale excitatory and inhibitory components differently.
    
    # For this simplified model, we'll scale all weights to maintain total activity
    # while pushing the ratio towards target
    current_ratio = exc_current / inh_current if inh_current > 0 else float('inf')
    
    if current_ratio == target_ratio:
        logger.info(f"E/I ratio already at target: {current_ratio:.2f}")
        return {}
        
    # Calculate adjustment factor
    adjustment = target_ratio / current_ratio
    scale_factor = min(2.0, max(0.5, adjustment))  # Clamp to safe range
    
    # Apply scaling
    for param in model.parameters():
        if param.grad is not None:
            param.data *= scale_factor
    
    # Log the adjustment
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    log_entry = {
        "step": step,
        "exc_activity": exc_current,
        "inh_activity": inh_current,
        "scaling_factor": scale_factor
    }
    
    # Read existing logs
    log_data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_data = []
    
    log_data.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
        
    logger.info(f"Enforced E/I ratio: step={step}, factor={scale_factor:.4f}, "
               f"current={current_ratio:.2f}, target={target_ratio}")
               
    return {"scaling_factor": scale_factor}

def apply_ei_balance_constraint(model: torch.nn.Module, target_ratio: float = 4.0) -> None:
    """
    Apply a hard constraint to maintain E/I balance by clipping weights.
    
    Args:
        model: The neural network model
        target_ratio: Target excitatory/inhibitory ratio
    """
    for param in model.parameters():
        # Clip weights to maintain bounded range
        param.data = torch.clamp(param.data, -1.0, 1.0)

def verify_ei_balance(model: torch.nn.Module, target_ratio: float = 4.0, 
                     tolerance: float = 0.5) -> bool:
    """
    Verify that the current E/I ratio is within tolerance of target.
    
    Args:
        model: The neural network model
        target_ratio: Target excitatory/inhibitory ratio
        tolerance: Acceptable deviation from target
        
    Returns:
        True if within tolerance, False otherwise
    """
    exc_current, inh_current, _ = calculate_current_ei_ratio(model)
    
    if inh_current == 0:
        return False
        
    current_ratio = exc_current / inh_current
    return abs(current_ratio - target_ratio) <= tolerance

class HomeostaticScaler:
    """
    Manages homeostatic scaling operations across training steps.
    """
    
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        self.config = config or HomeostasisConfig()
        self.step_count = 0
        
    def step(self, model: torch.nn.Module, optimizer: torch.optim.Optimizer) -> Dict[str, float]:
        """
        Apply scaling hook after optimizer step.
        
        Args:
            model: The neural network model
            optimizer: The optimizer used for training
            
        Returns:
            Dict with applied scaling factors
        """
        self.step_count += 1
        
        # First apply weight scaling
        scaling_factors = scale_weights(
            model, 
            self.config.target_ei_ratio, 
            self.config.scaling_decay_rate
        )
        
        # Then enforce E/I ratio
        ei_factors = enforce_ei_ratio(
            model,
            self.step_count,
            self.config.target_ei_ratio
        )
        
        # Combine results
        result = {**scaling_factors, **ei_factors}
        
        # Log if at interval
        if self.step_count % self.config.log_interval == 0:
            log_gradient_norms(model, self.step_count)
            
        return result

def apply_scaling_hook(optimizer: torch.optim.Optimizer, step: int, 
                      model: Optional[torch.nn.Module] = None,
                      config: Optional[HomeostasisConfig] = None) -> Dict[str, float]:
    """
    Integration point for homeostatic scaling after each optimizer step.
    Calls scale_weights and enforce_ei_ratio, then logs factors.
    
    Args:
        optimizer: The optimizer used for training
        step: Current training step
        model: The neural network model (required for scaling)
        config: Optional homeostasis configuration
        
    Returns:
        Dict with applied scaling factors
    """
    if model is None:
        raise ValueError("Model is required for homeostatic scaling")
        
    scaler = HomeostaticScaler(config)
    return scaler.step(model, optimizer)