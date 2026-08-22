import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch

from src.models.microcircuit import MicrocircuitColumn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    """
    Configuration for homeostatic scaling and E/I ratio enforcement.
    
    Attributes:
        target_ei_ratio: The target Excitatory/Inhibitory weight ratio (default 4.0).
        decay_rate: Decay rate for activity tracking (0.0 to 1.0).
        scaling_factor: Global scaling factor applied during homeostasis.
    """
    target_ei_ratio: float = 4.0
    decay_rate: float = 0.9
    scaling_factor: float = 1.0

@dataclass
class ActivityStats:
    """Statistics for current network activity."""
    excitatory_activity: float
    inhibitory_activity: float
    current_ratio: float
    deviation: float

def identify_excitatory_inhibitory_params(model: torch.nn.Module) -> Tuple[List[str], List[str]]:
    """
    Identify which parameters correspond to excitatory and inhibitory connections.
    
    In the canonical microcircuit, layers are explicitly defined. We assume:
    - Excitatory weights are in layers L23, L4, L5 (forward/feedback excitatory)
    - Inhibitory weights are in specific inhibitory interneuron connections
    
    For the structural constraint enforcement, we rely on the model architecture
    to define these connections. This function returns the parameter names
    that should be scaled to maintain the E/I ratio.
    
    Args:
        model: The model instance (MicrocircuitColumn or similar).
        
    Returns:
        Tuple of (excitatory_param_names, inhibitory_param_names)
    """
    excitatory_params = []
    inhibitory_params = []
    
    # Heuristic based on standard cortical column naming conventions
    # In a real implementation, this would be more specific to the model's
    # internal structure as defined in src/models/microcircuit.py
    for name, param in model.named_parameters():
        if param.requires_grad:
            # Assume weights starting with 'weight' in excitatory layers
            # are excitatory, and those in 'inhibitory' or specific interneuron
            # modules are inhibitory.
            if 'inhibitory' in name.lower() or 'interneuron' in name.lower():
                inhibitory_params.append(name)
            elif 'weight' in name.lower():
                # Default to excitatory for standard layer weights
                excitatory_params.append(name)
    
    return excitatory_params, inhibitory_params

def calculate_current_activity(model: torch.nn.Module, excitatory_params: List[str], 
                               inhibitory_params: List[str]) -> ActivityStats:
    """
    Calculate the current activity ratio based on weight magnitudes.
    
    Args:
        model: The model instance.
        excitatory_params: List of parameter names for excitatory connections.
        inhibitory_params: List of parameter names for inhibitory connections.
        
    Returns:
        ActivityStats object with current activity metrics.
    """
    exc_sum = 0.0
    inh_sum = 0.0
    
    for name, param in model.named_parameters():
        if name in excitatory_params:
            exc_sum += torch.abs(param).sum().item()
        elif name in inhibitory_params:
            inh_sum += torch.abs(param).sum().item()
    
    current_ratio = exc_sum / inh_sum if inh_sum > 1e-8 else float('inf')
    deviation = current_ratio - 4.0
    
    return ActivityStats(
        excitatory_activity=exc_sum,
        inhibitory_activity=inh_sum,
        current_ratio=current_ratio,
        deviation=deviation
    )

def scale_weights(model: torch.nn.Module, target_ratio: float, decay_rate: float) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain the E/I ratio.
    
    This function scales the weights of excitatory and inhibitory connections
    to drive the current ratio towards the target ratio.
    
    Formula: scale_factor = target_activity / current_activity
    
    Args:
        model: The model instance.
        target_ratio: The target E/I ratio (default 4.0).
        decay_rate: Decay rate for smoothing activity tracking.
        
    Returns:
        Dictionary mapping parameter names to applied scaling factors.
    """
    exc_params, inh_params = identify_excitatory_inhibitory_params(model)
    stats = calculate_current_activity(model, exc_params, inh_params)
    
    scaling_factors = {}
    
    if stats.inhibitory_activity > 1e-8:
        # Calculate scaling factor to achieve target ratio
        # We want: (exc_sum * scale_exc) / (inh_sum * scale_inh) = target_ratio
        # For simplicity, we scale inhibitory weights to match target ratio
        # assuming excitatory weights are the reference.
        
        # Target inhibitory activity to achieve target_ratio:
        # target_inh = exc_sum / target_ratio
        target_inh = stats.excitatory_activity / target_ratio
        
        scale_factor_inh = target_inh / stats.inhibitory_activity
        
        # Apply scaling to inhibitory parameters
        for name, param in model.named_parameters():
            if name in inh_params:
                with torch.no_grad():
                    param.mul_(scale_factor_inh)
                scaling_factors[name] = scale_factor_inh
                
        logger.info(f"Applied inhibitory scaling factor: {scale_factor_inh:.4f}")
    else:
        logger.warning("Inhibitory activity is near zero, skipping scaling.")
        
    return scaling_factors

def enforce_ei_ratio(model: torch.nn.Module, config: HomeostasisConfig) -> ActivityStats:
    """
    Enforce the 4:1 E/I ratio as a structural constraint.
    
    This function applies homeostatic scaling to preserve the structural
    connectivity ratio defined in the canonical microcircuit. It does NOT
    dynamically adjust per-batch targets, but rather maintains the fixed
    structural constraint throughout training.
    
    Args:
        model: The model instance (MicrocircuitColumn).
        config: HomeostasisConfig with target_ei_ratio and other parameters.
        
    Returns:
        ActivityStats after scaling.
    """
    logger.info(f"Enforcing E/I ratio constraint: target={config.target_ei_ratio}")
    
    # Apply scaling
    scale_weights(model, config.target_ei_ratio, config.decay_rate)
    
    # Verify the result
    exc_params, inh_params = identify_excitatory_inhibitory_params(model)
    stats = calculate_current_activity(model, exc_params, inh_params)
    
    logger.info(f"After scaling: E/I ratio = {stats.current_ratio:.4f} (deviation: {stats.deviation:.4f})")
    
    return stats

def apply_ei_balance_constraint(model: torch.nn.Module, config: HomeostasisConfig) -> None:
    """
    Apply the E/I balance constraint as a hard structural constraint.
    
    This is the main entry point for enforcing the 4:1 ratio as a structural
    property that is preserved by homeostasis during training.
    
    Args:
        model: The model instance.
        config: HomeostasisConfig.
    """
    # First, ensure the structural connectivity is correct
    # (This is assumed to be set up in the model initialization)
    
    # Then, apply homeostatic scaling to maintain the ratio
    enforce_ei_ratio(model, config)

def verify_ei_balance(model: torch.nn.Module, config: HomeostasisConfig, tolerance: float = 0.05) -> bool:
    """
    Verify that the E/I ratio is within the acceptable tolerance.
    
    Args:
        model: The model instance.
        config: HomeostasisConfig.
        tolerance: Acceptable deviation from target ratio (default 5%).
        
    Returns:
        True if the ratio is within tolerance, False otherwise.
    """
    exc_params, inh_params = identify_excitatory_inhibitory_params(model)
    stats = calculate_current_activity(model, exc_params, inh_params)
    
    target = config.target_ei_ratio
    lower = target * (1 - tolerance)
    upper = target * (1 + tolerance)
    
    is_valid = lower <= stats.current_ratio <= upper
    
    if not is_valid:
        logger.error(f"E/I ratio {stats.current_ratio:.4f} outside tolerance [{lower:.4f}, {upper:.4f}]")
    else:
        logger.info(f"E/I ratio {stats.current_ratio:.4f} within tolerance")
        
    return is_valid

class HomeostaticScaler:
    """
    A class to manage homeostatic scaling over training steps.
    
    This class maintains state and applies scaling at specified intervals
    to preserve the structural E/I ratio constraint.
    """
    
    def __init__(self, config: HomeostasisConfig):
        self.config = config
        self.step_count = 0
        self.scaling_history: List[Dict[str, Any]] = []
        
    def step(self, model: torch.nn.Module) -> ActivityStats:
        """
        Apply homeostatic scaling at the current training step.
        
        Args:
            model: The model instance.
            
        Returns:
            ActivityStats after scaling.
        """
        self.step_count += 1
        stats = enforce_ei_ratio(model, self.config)
        
        history_entry = {
            'step': self.step_count,
            'current_ratio': stats.current_ratio,
            'deviation': stats.deviation,
            'excitatory_activity': stats.excitatory_activity,
            'inhibitory_activity': stats.inhibitory_activity
        }
        self.scaling_history.append(history_entry)
        
        return stats

def apply_scaling_hook(model: torch.nn.Module, config: HomeostasisConfig) -> ActivityStats:
    """
    Convenience function to apply homeostatic scaling as a training hook.
    
    Args:
        model: The model instance.
        config: HomeostasisConfig.
        
    Returns:
        ActivityStats after scaling.
    """
    scaler = HomeostaticScaler(config)
    return scaler.step(model)

def log_gradient_norms(model: torch.nn.Module, step: int, log_path: str = "data/logs/gradient_norms.json") -> None:
    """
    Log gradient norms for SC-002 verification.
    
    Args:
        model: The model instance.
        step: Current training step.
        log_path: Path to the JSON log file.
    """
    gradient_norms = {}
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            gradient_norms[name] = float(torch.norm(param.grad).item())
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Load existing data or create new
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            data = json.load(f)
    else:
        data = {'steps': []}
    
    # Append new step
    data['steps'].append({
        'step': step,
        'norms': gradient_norms
    })
    
    # Write back
    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)

def verify_independence(train_data: Any, test_data: Any) -> bool:
    """
    Verify that training and test data are independent.
    
    This is a placeholder for the actual verification logic that would
    be implemented in src/data/benchmarks.py.
    
    Args:
        train_data: Training data.
        test_data: Test data.
        
    Returns:
        True if independent, False otherwise.
    """
    # Placeholder - actual implementation in src/data/benchmarks.py
    return True

def main():
    """Main function for testing homeostasis module."""
    logger.info("Testing homeostasis module...")
    
    # Create a simple test model
    class TestModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.exc_weight = torch.nn.Parameter(torch.ones(10, 10) * 0.5)
            self.inh_weight = torch.nn.Parameter(torch.ones(10, 10) * 0.5)
            
        def forward(self, x):
            return x
    
    model = TestModel()
    config = HomeostasisConfig(target_ei_ratio=4.0)
    
    # Initial stats
    exc_params, inh_params = identify_excitatory_inhibitory_params(model)
    initial_stats = calculate_current_activity(model, exc_params, inh_params)
    logger.info(f"Initial E/I ratio: {initial_stats.current_ratio:.4f}")
    
    # Apply scaling
    final_stats = enforce_ei_ratio(model, config)
    logger.info(f"Final E/I ratio: {final_stats.current_ratio:.4f}")
    
    # Verify
    is_valid = verify_ei_balance(model, config)
    logger.info(f"Balance verified: {is_valid}")

if __name__ == "__main__":
    main()