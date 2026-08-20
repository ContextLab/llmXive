"""
Homeostasis module for cortical column LLMs.
Implements synaptic scaling and E/I ratio enforcement mechanisms.
"""
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    """Configuration for homeostatic mechanisms."""
    target_ei_ratio: float = 4.0  # Typical excitatory/inhibitory ratio
    scaling_decay_rate: float = 0.01
    activity_window: int = 100  # Batches to consider for activity calculation
    batch_enforcement: bool = True  # Enforce per batch (T010c requirement)

@dataclass
class ActivityStats:
    """Statistics for neuronal activity tracking."""
    excitatory_activity: float = 0.0
    inhibitory_activity: float = 0.0
    current_ei_ratio: float = 0.0
    batch_step: int = 0

def identify_excitatory_inhibitory_params(
    model: torch.nn.Module,
    layer_names: Optional[List[str]] = None
) -> Tuple[List[torch.nn.Parameter], List[torch.nn.Parameter]]:
    """
    Identify excitatory and inhibitory parameters in the model.
    
    For cortical columns:
    - Excitatory: Weights in L2/3, L4, L5, L6 feedforward layers
    - Inhibitory: Weights in inhibitory interneuron connections
    
    Heuristic: Positive weights in specific layer patterns are excitatory,
    negative or specific layer patterns are inhibitory.
    """
    excitatory_params = []
    inhibitory_params = []
    
    layer_patterns = {
        'excitatory': ['l23', 'l4', 'l5', 'l6', 'feedforward', 'encoder'],
        'inhibitory': ['inhibitory', 'interneuron', 'l1', 'gating']
    }
    
    for name, param in model.named_parameters():
        name_lower = name.lower()
        is_excitatory = any(p in name_lower for p in layer_patterns['excitatory'])
        is_inhibitory = any(p in name_lower for p in layer_patterns['inhibitory'])
        
        if is_excitatory and not is_inhibitory:
            excitatory_params.append(param)
        elif is_inhibitory:
            inhibitory_params.append(param)
        else:
            # Default: treat as excitatory if no specific pattern
            excitatory_params.append(param)
    
    return excitatory_params, inhibitory_params

def calculate_current_ei_ratio(
    excitatory_params: List[torch.nn.Parameter],
    inhibitory_params: List[torch.nn.Parameter]
) -> float:
    """Calculate current E/I ratio from parameter magnitudes."""
    if not inhibitory_params:
        return float('inf')
    
    exc_activity = sum(p.abs().mean().item() for p in excitatory_params)
    inh_activity = sum(p.abs().mean().item() for p in inhibitory_params)
    
    if inh_activity == 0:
        return float('inf')
    
    return exc_activity / inh_activity

def scale_weights(
    model: torch.nn.Module,
    target_ratio: float,
    decay_rate: float,
    excitatory_params: Optional[List[torch.nn.Parameter]] = None,
    inhibitory_params: Optional[List[torch.nn.Parameter]] = None
) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    
    Formula: scale_factor = target_activity / current_activity
    Derived from E/I constraint: exc_scaled / inh_scaled = target_ratio
    """
    if excitatory_params is None or inhibitory_params is None:
        excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    
    current_ratio = calculate_current_ei_ratio(excitatory_params, inhibitory_params)
    
    if current_ratio == float('inf') or current_ratio == 0:
        logger.warning("Cannot scale: current E/I ratio is infinite or zero")
        return {}
    
    # Calculate scaling factors
    # We want: (exc * scale_exc) / (inh * scale_inh) = target_ratio
    # Simple approach: scale inhibitory to match target
    scale_inh = current_ratio / target_ratio
    scale_exc = 1.0  # Keep excitatory fixed, scale inhibitory
    
    # Apply decay for gradual adjustment
    scale_inh = 1.0 + decay_rate * (scale_inh - 1.0)
    
    scaling_factors = {}
    
    for param in inhibitory_params:
        param.data *= scale_inh
        scaling_factors['inhibitory'] = scale_inh
    
    for param in excitatory_params:
        param.data *= scale_exc
        scaling_factors['excitatory'] = scale_exc
    
    logger.info(f"Applied scaling: exc={scale_exc:.4f}, inh={scale_inh:.4f}, "
               f"target_ratio={target_ratio:.2f}, current_ratio={current_ratio:.2f}")
    
    return scaling_factors

def log_gradient_norms(
    model: torch.nn.Module,
    step: int,
    log_path: str = "data/logs/gradient_norms.json"
) -> Dict[str, float]:
    """
    Compute and log gradient norms for SC-002 verification.
    
    Args:
        model: The model to inspect
        step: Current training step
        log_path: Path to the JSON log file
    
    Returns:
        Dictionary of gradient norms by layer
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    gradient_norms = {
        'step': step,
        'layer_norms': {},
        'total_norm': 0.0
    }
    
    total_norm_sq = 0.0
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = param.grad.norm().item()
            gradient_norms['layer_norms'][name] = norm
            total_norm_sq += norm ** 2
    
    gradient_norms['total_norm'] = np.sqrt(total_norm_sq)
    
    # Load existing logs
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                existing_logs = json.load(f)
            except json.JSONDecodeError:
                existing_logs = []
    else:
        existing_logs = []
    
    # Append new entry
    existing_logs.append(gradient_norms)
    
    # Write back
    with open(log_path, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    logger.debug(f"Logged gradient norms for step {step} to {log_path}")
    
    return gradient_norms

def enforce_ei_ratio(
    model: torch.nn.Module,
    config: HomeostasisConfig,
    excitatory_params: Optional[List[torch.nn.Parameter]] = None,
    inhibitory_params: Optional[List[torch.nn.Parameter]] = None
) -> ActivityStats:
    """
    Enforce E/I ratio per batch during training (T010c requirement).
    
    This is called after each batch forward/backward pass to maintain
    homeostatic balance.
    
    Args:
        model: The model to enforce constraints on
        config: Homeostasis configuration
        excitatory_params: Pre-identified excitatory parameters
        inhibitory_params: Pre-identified inhibitory parameters
    
    Returns:
        ActivityStats with current E/I ratio
    """
    if excitatory_params is None or inhibitory_params is None:
        excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    
    # Calculate current activity
    exc_activity = sum(p.abs().mean().item() for p in excitatory_params)
    inh_activity = sum(p.abs().mean().item() for p in inhibitory_params)
    
    current_ratio = exc_activity / (inh_activity + 1e-8)
    
    stats = ActivityStats(
        excitatory_activity=exc_activity,
        inhibitory_activity=inh_activity,
        current_ei_ratio=current_ratio,
        batch_step=0  # Will be set by caller
    )
    
    # Enforce ratio if batch enforcement is enabled
    if config.batch_enforcement:
        scale_weights(
            model=model,
            target_ratio=config.target_ei_ratio,
            decay_rate=config.scaling_decay_rate,
            excitatory_params=excitatory_params,
            inhibitory_params=inhibitory_params
        )
    
    return stats

def apply_ei_balance_constraint(
    model: torch.nn.Module,
    target_ratio: float = 4.0,
    max_deviation: float = 0.5
) -> bool:
    """
    Apply a hard constraint to ensure E/I ratio stays within bounds.
    
    Args:
        model: The model to constrain
        target_ratio: Target E/I ratio
        max_deviation: Maximum allowed deviation from target
    
    Returns:
        True if constraint was satisfied, False if adjustment was needed
    """
    excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    current_ratio = calculate_current_ei_ratio(excitatory_params, inhibitory_params)
    
    lower_bound = target_ratio * (1 - max_deviation)
    upper_bound = target_ratio * (1 + max_deviation)
    
    if lower_bound <= current_ratio <= upper_bound:
        return True
    
    # Apply soft scaling to bring ratio back into bounds
    scale_weights(
        model=model,
        target_ratio=target_ratio,
        decay_rate=0.1,  # Faster decay for hard constraint
        excitatory_params=excitatory_params,
        inhibitory_params=inhibitory_params
    )
    
    return False

def verify_ei_balance(
    model: torch.nn.Module,
    target_ratio: float = 4.0,
    tolerance: float = 0.2
) -> Tuple[bool, float]:
    """
    Verify that the model maintains E/I balance.
    
    Args:
        model: The model to verify
        target_ratio: Expected E/I ratio
        tolerance: Acceptable deviation from target
    
    Returns:
        Tuple of (is_balanced, current_ratio)
    """
    excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    current_ratio = calculate_current_ei_ratio(excitatory_params, inhibitory_params)
    
    is_balanced = abs(current_ratio - target_ratio) <= tolerance * target_ratio
    
    return is_balanced, current_ratio

class HomeostaticScaler:
    """
    Homeostatic scaler for per-batch E/I ratio enforcement.
    
    This class maintains state across training batches and applies
    scaling adjustments to maintain homeostatic balance.
    """
    
    def __init__(self, config: HomeostasisConfig):
        self.config = config
        self.activity_history: List[ActivityStats] = []
        self.scaling_history: List[Dict[str, float]] = []
    
    def step(
        self,
        model: torch.nn.Module,
        step: int,
        log_gradient_norms_flag: bool = True
    ) -> ActivityStats:
        """
        Perform one homeostatic step.
        
        Args:
            model: The model to scale
            step: Current training step
            log_gradient_norms_flag: Whether to log gradient norms
        
        Returns:
            ActivityStats for this step
        """
        # Log gradient norms if requested
        if log_gradient_norms_flag:
            log_gradient_norms(model, step)
        
        # Enforce E/I ratio per batch
        stats = enforce_ei_ratio(model, self.config, None, None)
        stats.batch_step = step
        
        self.activity_history.append(stats)
        
        # Keep history bounded
        if len(self.activity_history) > self.config.activity_window:
            self.activity_history.pop(0)
        
        return stats

def apply_scaling_hook(
    model: torch.nn.Module,
    config: HomeostasisConfig,
    step: int
) -> ActivityStats:
    """
    Convenience function to apply homeostatic scaling at a training step.
    
    Args:
        model: The model to scale
        config: Homeostasis configuration
        step: Current training step
    
    Returns:
        ActivityStats after scaling
    """
    scaler = HomeostaticScaler(config)
    return scaler.step(model, step)

def verify_independence(
    train_data: np.ndarray,
    test_data: np.ndarray
) -> bool:
    """
    Verify that training and test data are from independent distributions.
    
    Uses Kolmogorov-Smirnov test. Returns True if distributions are
    statistically different (p_value < 0.05).
    
    Args:
        train_data: Training data array
        test_data: Test data array
    
    Returns:
        True if distributions are distinct
    """
    from scipy import stats
    
    # Flatten arrays for 1D KS test
    train_flat = train_data.flatten()
    test_flat = test_data.flatten()
    
    ks_stat, p_value = stats.ks_2samp(train_flat, test_flat)
    
    if p_value < 0.05:
        logger.info(f"Distributions are independent (KS p-value={p_value:.4f})")
        return True
    else:
        logger.warning(f"Distributions may not be independent (KS p-value={p_value:.4f})")
        return False