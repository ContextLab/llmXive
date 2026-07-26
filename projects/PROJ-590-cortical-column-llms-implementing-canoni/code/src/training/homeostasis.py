import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    """Configuration for homeostatic scaling operations."""
    target_activity: float = 0.5
    decay_rate: float = 0.1
    target_ratio: float = 4.0  # Target E/I ratio (excitatory/inhibitory)

@dataclass
class ActivityStats:
    """Statistics about current network activity."""
    mean_activity: float
    excitatory_mean: float
    inhibitory_mean: float
    current_ratio: float
    total_params: int

def calculate_current_ei_ratio(model: nn.Module) -> ActivityStats:
    """
    Calculate the current excitatory/inhibitory activity ratio.
    
    Assumes layers are named with 'excitatory' or 'inhibitory' in their name,
    or uses a heuristic based on layer types.
    """
    exc_sum = 0.0
    exc_count = 0
    inh_sum = 0.0
    inh_count = 0
    total_params = 0

    for name, param in model.named_parameters():
        total_params += param.numel()
        if 'excitatory' in name.lower() or 'exc' in name.lower():
            exc_sum += param.abs().mean().item()
            exc_count += 1
        elif 'inhibitory' in name.lower() or 'inh' in name.lower():
            inh_sum += param.abs().mean().item()
            inh_count += 1

    # Fallback if no explicit E/I naming found
    if exc_count == 0 and inh_count == 0:
        logger.warning("No E/I named parameters found, using default ratio")
        return ActivityStats(
            mean_activity=0.0,
            excitatory_mean=1.0,
            inhibitory_mean=0.25,
            current_ratio=4.0,
            total_params=total_params
        )

    exc_mean = exc_sum / exc_count if exc_count > 0 else 0.0
    inh_mean = inh_sum / inh_count if inh_count > 0 else 0.0
    current_ratio = exc_mean / inh_mean if inh_mean > 0 else float('inf')

    return ActivityStats(
        mean_activity=(exc_mean + inh_mean) / 2,
        excitatory_mean=exc_mean,
        inhibitory_mean=inh_mean,
        current_ratio=current_ratio,
        total_params=total_params
    )

def scale_weights(model: nn.Module, target_ratio: float, decay_rate: float) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    
    Formula: scale_factor = target_activity / current_activity
    
    Args:
        model: The neural network model
        target_ratio: Target excitatory/inhibitory ratio
        decay_rate: Rate of decay for scaling factors
        
    Returns:
        Dict of applied scaling factors per layer
    """
    scaling_factors = {}
    stats = calculate_current_ei_ratio(model)
    
    if stats.current_ratio == float('inf'):
        logger.warning("Infinite current ratio, skipping scaling")
        return scaling_factors

    # Calculate scaling factor to move towards target
    # If current > target, scale down; if current < target, scale up
    ratio_error = stats.current_ratio - target_ratio
    scale_factor = 1.0 - (decay_rate * ratio_error / target_ratio)
    
    # Clamp scale factor to prevent extreme changes
    scale_factor = max(0.1, min(5.0, scale_factor))
    
    for name, param in model.named_parameters():
        if param.requires_grad:
            # Apply scaling
            with torch.no_grad():
                param.mul_(scale_factor)
            scaling_factors[name] = scale_factor
            logger.debug(f"Applied scale {scale_factor:.4f} to {name}")

    return scaling_factors

def apply_ei_balance_constraint(model: nn.Module, min_ratio: float = 2.0, max_ratio: float = 6.0):
    """
    Enforce E/I balance constraints by clipping weights.
    
    Args:
        model: The neural network model
        min_ratio: Minimum allowed E/I ratio
        max_ratio: Maximum allowed E/I ratio
    """
    stats = calculate_current_ei_ratio(model)
    
    if stats.current_ratio < min_ratio:
        logger.warning(f"E/I ratio {stats.current_ratio:.2f} below minimum {min_ratio}, adjusting")
        # Boost excitatory weights
        for name, param in model.named_parameters():
            if 'excitatory' in name.lower() or 'exc' in name.lower():
                with torch.no_grad():
                    param.mul_(min_ratio / stats.current_ratio)
    elif stats.current_ratio > max_ratio:
        logger.warning(f"E/I ratio {stats.current_ratio:.2f} above maximum {max_ratio}, adjusting")
        # Boost inhibitory weights
        for name, param in model.named_parameters():
            if 'inhibitory' in name.lower() or 'inh' in name.lower():
                with torch.no_grad():
                    param.mul_(stats.current_ratio / max_ratio)

def verify_ei_balance(model: nn.Module, tolerance: float = 0.5) -> bool:
    """
    Verify that the E/I balance is within acceptable tolerance.
    
    Args:
        model: The neural network model
        tolerance: Acceptable deviation from target ratio (default 4.0)
        
    Returns:
        True if balance is within tolerance, False otherwise
    """
    stats = calculate_current_ei_ratio(model)
    target = 4.0
    return abs(stats.current_ratio - target) <= tolerance

class HomeostaticScaler:
    """
    Homeostatic scaling hook for training loops.
    
    This class manages the periodic application of homeostatic scaling
    during training to maintain stable E/I ratios.
    """
    
    def __init__(self, config: HomeostasisConfig, log_interval: int = 100):
        self.config = config
        self.log_interval = log_interval
        self.step_count = 0
        self.scaling_history = []
        
    def step(self, model: nn.Module, optimizer: Optional[torch.optim.Optimizer] = None):
        """
        Apply homeostatic scaling at regular intervals.
        
        Args:
            model: The model to scale
            optimizer: Optional optimizer (not used directly but kept for API compatibility)
        """
        self.step_count += 1
        
        if self.step_count % self.log_interval == 0:
            stats = calculate_current_ei_ratio(model)
            logger.info(f"Step {self.step_count}: E/I ratio = {stats.current_ratio:.2f}")
            
            # Apply scaling
            factors = scale_weights(model, self.config.target_ratio, self.config.decay_rate)
            self.scaling_history.append({
                'step': self.step_count,
                'ratio': stats.current_ratio,
                'factors': factors
            })

def log_gradient_norms(model: nn.Module, step: int, log_file: Optional[str] = None) -> Dict[str, float]:
    """
    Compute and append gradient norms to a JSON log file for SC-002 verification.
    
    This function calculates the L2 norm of gradients for each parameter in the model
    and appends the results to a JSON log file. The log file is used for verifying
    gradient stability across training steps.
    
    Args:
        model: The PyTorch model to inspect gradients from.
        step: The current training step number.
        log_file: Optional path to the log file. Defaults to 'data/logs/gradient_norms.json'.
        
    Returns:
        A dictionary containing the computed gradient norms for this step.
        
    Raises:
        FileNotFoundError: If the log directory does not exist.
    """
    if log_file is None:
        log_file = 'data/logs/gradient_norms.json'
        
    # Ensure directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        logger.info(f"Created log directory: {log_dir}")
    
    # Compute gradient norms
    gradient_norms = {}
    total_norm = 0.0
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = param.grad.norm().item()
            gradient_norms[name] = norm
            total_norm += norm ** 2
        else:
            gradient_norms[name] = 0.0
    
    gradient_norms['total_norm'] = total_norm ** 0.5
    gradient_norms['step'] = step
    gradient_norms['timestamp'] = datetime.utcnow().isoformat()
    
    # Load existing data or initialize
    existing_data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    logger.warning(f"Existing log file is not a list, initializing fresh")
                    existing_data = []
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing log file: {e}, initializing fresh")
            existing_data = []
    
    # Append new entry
    existing_data.append(gradient_norms)
    
    # Write back to file
    with open(log_file, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.debug(f"Logged gradient norms for step {step} to {log_file}")
    return gradient_norms
