import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    """Configuration for homeostatic scaling and E/I ratio enforcement."""
    target_ei_ratio: float = 4.0
    decay_rate: float = 0.01
    scaling_window: int = 100
    activity_threshold: float = 0.1
    structural_constraint: bool = True  # Enforce fixed ratio as structural constraint

@dataclass
class ActivityStats:
    """Statistics for current network activity."""
    excitatory_activity: float
    inhibitory_activity: float
    total_activity: float
    ei_ratio: float

def identify_excitatory_inhibitory_params(model: torch.nn.Module) -> Tuple[List[str], List[str]]:
    """
    Identify excitatory and inhibitory parameters based on layer naming conventions.
    
    Excitatory: weights from L4->L2/3, L2/3->L5, L5->L6, L2/3 recurrent
    Inhibitory: weights from L2/3->L2/3 (inhibitory interneurons)
    
    Returns:
        Tuple of (excitatory_param_names, inhibitory_param_names)
    """
    excitatory_params = []
    inhibitory_params = []
    
    for name, param in model.named_parameters():
        name_lower = name.lower()
        # Excitatory connections follow feedforward and recurrent excitatory paths
        if any(keyword in name_lower for keyword in ['excitatory', 'e_', 'l4', 'l5', 'l6', 'recurrent']):
            if 'inhibitory' not in name_lower and 'i_' not in name_lower:
                excitatory_params.append(name)
        # Inhibitory connections are explicitly marked or follow inhibitory interneuron paths
        elif any(keyword in name_lower for keyword in ['inhibitory', 'i_', 'interneuron']):
            inhibitory_params.append(name)
    
    return excitatory_params, inhibitory_params

def calculate_current_activity(model: torch.nn.Module, excitatory_params: List[str], 
                               inhibitory_params: List[str]) -> ActivityStats:
    """
    Calculate current network activity levels from parameter magnitudes.
    
    Args:
        model: The neural network model
        excitatory_params: List of excitatory parameter names
        inhibitory_params: List of inhibitory parameter names
        
    Returns:
        ActivityStats object with current activity measurements
    """
    exc_activity = 0.0
    inh_activity = 0.0
    
    for name, param in model.named_parameters():
        if name in excitatory_params:
            exc_activity += torch.norm(param).item()
        elif name in inhibitory_params:
            inh_activity += torch.norm(param).item()
    
    total_activity = exc_activity + inh_activity
    ei_ratio = exc_activity / inh_activity if inh_activity > 0 else float('inf')
    
    return ActivityStats(
        excitatory_activity=exc_activity,
        inhibitory_activity=inh_activity,
        total_activity=total_activity,
        ei_ratio=ei_ratio
    )

def scale_weights(model: torch.nn.Module, target_ratio: float, decay_rate: float,
                 structural_constraint: bool = True) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    
    This function implements homeostatic scaling by adjusting weights to restore
    target activity levels. The scaling factor is derived from the ratio of
    target to current activity.
    
    Args:
        model: The neural network model
        target_ratio: Target E/I activity ratio (default 4.0)
        decay_rate: Rate of decay for scaling adjustments
        structural_constraint: If True, enforce fixed ratio as structural constraint
        
    Returns:
        Dictionary of applied scaling factors per parameter
    """
    excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    current_stats = calculate_current_activity(model, excitatory_params, inhibitory_params)
    
    scaling_factors = {}
    
    if structural_constraint:
        # Structural constraint: maintain fixed connectivity pattern
        # Scale inhibitory weights to match target ratio while preserving excitatory structure
        if current_stats.inhibitory_activity > 0:
            scale_factor = (target_ratio * current_stats.excitatory_activity) / current_stats.inhibitory_activity
            scale_factor = min(max(scale_factor, 0.5), 2.0)  # Clamp to reasonable range
            
            for name, param in model.named_parameters():
                if name in inhibitory_params:
                    param.data *= scale_factor
                    scaling_factors[name] = scale_factor
                    logger.debug(f"Scaled inhibitory param {name} by {scale_factor:.4f}")
    else:
        # Dynamic adjustment: scale both exc and inh based on deviation from target
        if current_stats.ei_ratio > target_ratio:
            # Too much excitation, scale down excitatory or scale up inhibitory
            for name, param in model.named_parameters():
                if name in excitatory_params:
                    scale_factor = target_ratio / current_stats.ei_ratio
                    param.data *= (1 - decay_rate * (1 - scale_factor))
                    scaling_factors[name] = 1 - decay_rate * (1 - scale_factor)
        elif current_stats.ei_ratio < target_ratio:
            # Too much inhibition, scale down inhibitory or scale up excitatory
            for name, param in model.named_parameters():
                if name in inhibitory_params:
                    scale_factor = current_stats.ei_ratio / target_ratio
                    param.data *= (1 - decay_rate * (1 - scale_factor))
                    scaling_factors[name] = 1 - decay_rate * (1 - scale_factor)
    
    return scaling_factors

def enforce_ei_ratio(model: torch.nn.Module, config: HomeostasisConfig) -> Dict[str, float]:
    """
    Enforce E/I ratio as a structural constraint that is preserved during training.
    
    This function implements the core requirement of T010c: the E/I ratio is enforced
    as a FIXED structural constraint (fixed connectivity) that is PRESERVED by 
    homeostasis during training, NOT a dynamic per-batch target adjustment.
    
    The constraint is structural because:
    1. The connectivity pattern (which connections are excitatory vs inhibitory) is fixed
    2. The ratio is maintained by scaling weights within their structural roles
    3. The constraint is preserved across training steps, not adjusted per batch
    
    Args:
        model: The neural network model
        config: HomeostasisConfig with target_ei_ratio and structural_constraint flag
        
    Returns:
        Dictionary of applied scaling factors
    """
    if not config.structural_constraint:
        logger.warning("structural_constraint is False, using dynamic adjustment instead of fixed ratio")
    
    excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    
    # Calculate current activity
    current_stats = calculate_current_activity(model, excitatory_params, inhibitory_params)
    
    # Enforce fixed ratio by scaling inhibitory weights to match target
    # This preserves the structural connectivity while maintaining the ratio
    scaling_factors = {}
    
    if current_stats.inhibitory_activity > 0:
        # Target: excitatory_activity / inhibitory_activity = target_ei_ratio
        # So: inhibitory_activity = excitatory_activity / target_ei_ratio
        # Scale factor for inhibitory weights: target_inh / current_inh
        target_inh_activity = current_stats.excitatory_activity / config.target_ei_ratio
        scale_factor = target_inh_activity / current_stats.inhibitory_activity
        
        # Clamp scale factor to prevent extreme adjustments
        scale_factor = min(max(scale_factor, 0.1), 10.0)
        
        for name, param in model.named_parameters():
            if name in inhibitory_params:
                param.data *= scale_factor
                scaling_factors[name] = scale_factor
                logger.debug(f"Structural E/I enforcement: scaled {name} by {scale_factor:.4f}")
    
    return scaling_factors

def apply_ei_balance_constraint(model: torch.nn.Module, config: HomeostasisConfig) -> None:
    """
    Apply E/I balance constraint as a structural preservation mechanism.
    
    This function ensures that the E/I ratio constraint is maintained as a 
    structural property of the network, consistent with the cortical column
    architecture where excitatory and inhibitory connections have fixed roles.
    
    Args:
        model: The neural network model
        config: HomeostasisConfig
    """
    scale_weights(model, config.target_ei_ratio, config.decay_rate, 
                structural_constraint=config.structural_constraint)

def verify_ei_balance(model: torch.nn.Module, config: HomeostasisConfig, 
                     tolerance: float = 0.05) -> Tuple[bool, float]:
    """
    Verify that the current E/I ratio is within tolerance of the target.
    
    Args:
        model: The neural network model
        config: HomeostasisConfig
        tolerance: Acceptable deviation from target ratio (default 5%)
        
    Returns:
        Tuple of (is_balanced, current_ratio)
    """
    excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    current_stats = calculate_current_activity(model, excitatory_params, inhibitory_params)
    
    target_ratio = config.target_ei_ratio
    current_ratio = current_stats.ei_ratio
    
    # Check if current ratio is within tolerance of target
    lower_bound = target_ratio * (1 - tolerance)
    upper_bound = target_ratio * (1 + tolerance)
    
    is_balanced = lower_bound <= current_ratio <= upper_bound
    
    logger.info(f"E/I Balance Check: target={target_ratio}, current={current_ratio:.4f}, "
               f"tolerance={tolerance}, balanced={is_balanced}")
    
    return is_balanced, current_ratio

class HomeostaticScaler:
    """
    Homeostatic scaler that maintains E/I ratio as a structural constraint.
    
    This class implements the persistent enforcement of E/I balance across 
    training steps, treating the ratio as a fixed structural property rather
    than a dynamic per-batch adjustment.
    """
    
    def __init__(self, config: HomeostasisConfig):
        self.config = config
        self.step_count = 0
        self.scaling_history = []
    
    def apply_scaling_hook(self, model: torch.nn.Module, step: int) -> Dict[str, float]:
        """
        Apply homeostatic scaling at a specific training step.
        
        Args:
            model: The neural network model
            step: Current training step
            
        Returns:
            Dictionary of applied scaling factors
        """
        self.step_count = step
        
        # Only apply scaling at configured intervals
        if step % self.config.scaling_window != 0:
            return {}
        
        scaling_factors = enforce_ei_ratio(model, self.config)
        self.scaling_history.append({
            'step': step,
            'factors': scaling_factors
        })
        
        # Verify balance after scaling
        is_balanced, current_ratio = verify_ei_balance(model, self.config)
        if not is_balanced:
            logger.warning(f"Step {step}: E/I balance not achieved after scaling. "
                         f"Current ratio: {current_ratio:.4f}, Target: {self.config.target_ei_ratio}")
        
        return scaling_factors

def apply_scaling_hook(model: torch.nn.Module, config: HomeostasisConfig, 
                      step: int) -> Dict[str, float]:
    """
    Convenience function to apply homeostatic scaling.
    
    Args:
        model: The neural network model
        config: HomeostasisConfig
        step: Current training step
        
    Returns:
        Dictionary of applied scaling factors
    """
    scaler = HomeostaticScaler(config)
    return scaler.apply_scaling_hook(model, step)

def log_gradient_norms(model: torch.nn.Module, step: int) -> None:
    """
    Compute and append gradient norms to data/logs/gradient_norms.json.
    
    This function satisfies SC-002 by logging gradient norms for verification.
    
    Args:
        model: The neural network model
        step: Current training step
    """
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "gradient_norms.json")
    
    norms = {}
    for name, param in model.named_parameters():
        if param.grad is not None:
            norm = torch.norm(param.grad).item()
            norms[name] = norm
    
    # Load existing logs or create new
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []
    
    # Append new entry
    logs.append({
        'step': step,
        'norms': norms
    })
    
    # Write back
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    logger.debug(f"Logged gradient norms for step {step} to {log_file}")

def verify_independence(train_data: Any, test_data: Any) -> bool:
    """
    Verify that training and test data are independent.
    
    This is a placeholder for data independence verification.
    
    Args:
        train_data: Training data
        test_data: Test data
        
    Returns:
        True if data is independent, False otherwise
    """
    # Implementation would check statistical independence
    # For now, return True as a placeholder
    return True

def main():
    """Main entry point for homeostasis module."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Homeostasis module loaded successfully")

if __name__ == "__main__":
    main()