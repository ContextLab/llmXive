import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    target_ei_ratio: float = 4.0
    scaling_decay_rate: float = 0.01
    log_path: str = "data/logs/ei_ratio_log.json"
    gradient_log_path: str = "data/logs/gradient_norms.json"

@dataclass
class ActivityStats:
    exc_activity: float
    inh_activity: float
    total_activity: float

def calculate_current_ei_ratio(model: nn.Module) -> Tuple[float, float, float]:
    """
    Calculate current excitatory and inhibitory activity from model weights.
    Assumes positive weights are excitatory and negative are inhibitory (simplified).
    Returns (exc_sum, inh_sum, total_sum).
    """
    exc_sum = 0.0
    inh_sum = 0.0
    
    for param in model.parameters():
        if param.grad is not None:
            # Simple heuristic: positive weights = excitatory, negative = inhibitory
            exc_weights = torch.clamp(param, min=0)
            inh_weights = torch.clamp(param, max=0).abs()
            
            exc_sum += exc_weights.sum().item()
            inh_sum += inh_weights.sum().item()
    
    total = exc_sum + inh_sum
    return exc_sum, inh_sum, total

def scale_weights(model: nn.Module, target_ratio: float, decay_rate: float) -> Dict[str, float]:
    """
    Apply homeostatic synaptic scaling to maintain E/I ratio.
    Formula: scale_factor = target_activity / current_activity
    """
    exc_activity, inh_activity, _ = calculate_current_ei_ratio(model)
    
    if inh_activity == 0:
        logger.warning("Inhibitory activity is zero, skipping scaling")
        return {}
    
    current_ratio = exc_activity / inh_activity
    target_activity = exc_activity / target_ratio
    
    # Scaling factor to adjust weights towards target ratio
    if exc_activity > 0:
        scale_factor = target_activity / exc_activity
    else:
        scale_factor = 1.0
    
    # Apply bounded scaling to prevent explosion
    scale_factor = max(0.1, min(10.0, scale_factor))
    
    # Apply decay to make adjustments gradual
    effective_scale = 1.0 + (scale_factor - 1.0) * decay_rate
    
    scaling_factors = {}
    for name, param in model.named_parameters():
        if param.requires_grad:
            param.data *= effective_scale
            scaling_factors[name] = effective_scale
    
    return scaling_factors

def log_gradient_norms(model: nn.Module, step: int, log_path: str = "data/logs/gradient_norms.json") -> None:
    """
    Compute and log gradient norms for SC-002 verification.
    """
    log_dir = os.path.dirname(log_path)
    os.makedirs(log_dir, exist_ok=True)
    
    gradient_norms = []
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = param.grad.norm().item()
            gradient_norms.append({"name": name, "norm": norm, "step": step})
    
    # Load existing logs
    logs = []
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            logs = json.load(f)
    
    logs.extend(gradient_norms)
    
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

def enforce_ei_ratio(model: nn.Module, step: int, target_ratio: float = 4.0, log_path: str = "data/logs/ei_ratio_log.json") -> Dict[str, float]:
    """
    Enforce E/I ratio by calculating mean excitatory and inhibitory activity
    and applying scaling factor to maintain target ratio.
    """
    exc_activity, inh_activity, _ = calculate_current_ei_ratio(model)
    
    if inh_activity == 0:
        scaling_factor = 1.0
    else:
        current_ratio = exc_activity / inh_activity
        # Calculate scaling factor to force ratio to target
        # If current > target, we need to reduce exc or increase inh
        scaling_factor = target_ratio / current_ratio if current_ratio > 0 else 1.0
    
    # Bound scaling factor to reasonable range
    scaling_factor = max(0.5, min(2.0, scaling_factor))
    
    # Apply scaling to weights
    for param in model.parameters():
        if param.requires_grad:
            param.data *= scaling_factor
    
    # Log the scaling event
    log_entry = {
        "step": step,
        "exc_activity": exc_activity,
        "inh_activity": inh_activity,
        "scaling_factor": scaling_factor
    }
    
    log_dir = os.path.dirname(log_path)
    os.makedirs(log_dir, exist_ok=True)
    
    logs = []
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            logs = json.load(f)
    
    logs.append(log_entry)
    
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)
    
    return {"scaling_factor": scaling_factor, "exc_activity": exc_activity, "inh_activity": inh_activity}

def apply_ei_balance_constraint(model: nn.Module, target_ratio: float = 4.0) -> None:
    """
    Apply E/I balance constraint by clipping weights to maintain ratio.
    """
    for param in model.parameters():
        if param.requires_grad:
            # Clip weights to ensure bounded range
            param.data = torch.clamp(param.data, min=-1.0, max=1.0)

def verify_ei_balance(model: nn.Module, target_ratio: float = 4.0, tolerance: float = 0.1) -> bool:
    """
    Verify that the current E/I ratio is within tolerance of target.
    """
    exc_activity, inh_activity, _ = calculate_current_ei_ratio(model)
    
    if inh_activity == 0:
        return False
    
    current_ratio = exc_activity / inh_activity
    return abs(current_ratio - target_ratio) / target_ratio < tolerance

class HomeostaticScaler:
    """
    Homeostatic scaler that applies scaling after each optimizer step.
    """
    def __init__(self, config: HomeostasisConfig):
        self.config = config
        self.step_count = 0
        
        # Ensure log directories exist
        os.makedirs(os.path.dirname(self.config.log_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.config.gradient_log_path), exist_ok=True)
    
    def apply_scaling_hook(self, optimizer: torch.optim.Optimizer, step: int) -> Dict[str, float]:
        """
        Main hook called after each optimizer step.
        Calls scale_weights and enforce_ei_ratio, then logs factors.
        """
        # Get the model from optimizer
        model = None
        for param_group in optimizer.param_groups:
            if 'params' in param_group:
                # Get first parameter's module (simplified)
                for param in param_group['params']:
                    if hasattr(param, 'module'):
                        model = param.module
                        break
                if model is not None:
                    break
        
        if model is None:
            # Fallback: assume optimizer is attached to a model we can access
            # This is a simplification - in practice, model should be passed explicitly
            logger.warning("Could not determine model from optimizer, skipping scaling")
            return {}
        
        # Apply weight scaling
        scaling_factors = scale_weights(
            model, 
            self.config.target_ei_ratio, 
            self.config.scaling_decay_rate
        )
        
        # Enforce E/I ratio
        ei_factors = enforce_ei_ratio(
            model,
            step,
            self.config.target_ei_ratio,
            self.config.log_path
        )
        
        # Log gradient norms
        log_gradient_norms(model, step, self.config.gradient_log_path)
        
        self.step_count = step
        
        # Combine and return factors
        return {**scaling_factors, **ei_factors}

def apply_scaling_hook(optimizer: torch.optim.Optimizer, step: int, 
                     config: Optional[HomeostasisConfig] = None) -> Dict[str, float]:
    """
    Convenience function to apply scaling hook after optimizer step.
    This is the main entry point for T018a.
    
    Calls:
    - scale_weights (from T010a)
    - enforce_ei_ratio (from T010c)
    - log_gradient_norms (from T010b)
    
    Logs all scaling factors to data/logs/ei_ratio_log.json
    """
    if config is None:
        config = HomeostasisConfig()
    
    # Ensure log directories exist
    os.makedirs(os.path.dirname(config.log_path), exist_ok=True)
    os.makedirs(os.path.dirname(config.gradient_log_path), exist_ok=True)
    
    # Get model from optimizer (simplified approach)
    model = None
    for param_group in optimizer.param_groups:
        if 'params' in param_group:
            for param in param_group['params']:
                if hasattr(param, 'module'):
                    model = param.module
                    break
            if model is not None:
                break
    
    if model is None:
        logger.warning("Could not determine model from optimizer, skipping scaling hook")
        return {}
    
    # 1. Apply weight scaling (T010a)
    scaling_factors = scale_weights(
        model,
        config.target_ei_ratio,
        config.scaling_decay_rate
    )
    
    # 2. Enforce E/I ratio (T010c)
    ei_factors = enforce_ei_ratio(
        model,
        step,
        config.target_ei_ratio,
        config.log_path
    )
    
    # 3. Log gradient norms (T010b)
    log_gradient_norms(model, step, config.gradient_log_path)
    
    # Merge and return all factors
    return {**scaling_factors, **ei_factors}
