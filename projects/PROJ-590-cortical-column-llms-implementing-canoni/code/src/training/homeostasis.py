import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch
import torch.nn as nn

# Ensure log directory exists
LOG_DIR = "data/logs"
GRADIENT_LOG_PATH = os.path.join(LOG_DIR, "gradient_norms.json")

logger = logging.getLogger(__name__)

@dataclass
class HomeostasisConfig:
    target_ei_ratio: float = 4.0
    decay_rate: float = 0.01
    activity_threshold: float = 0.1

@dataclass
class ActivityStats:
    total_activity: float
    excitatory_activity: float
    inhibitory_activity: float
    current_ratio: float

def identify_excitatory_inhibitory_params(model: nn.Module) -> Tuple[List[str], List[str]]:
    """
    Identify parameters as excitatory or inhibitory based on naming conventions.
    In a real biological model, this would be explicit. Here we use heuristics:
    - 'weight' parameters are typically excitatory if they connect layers
    - We assume a simple heuristic: weights in 'attention' or 'mlp' are excitatory
    - Biases or specific 'inhibitory' named params are inhibitory
    """
    excitatory = []
    inhibitory = []
    
    for name, param in model.named_parameters():
        # Heuristic: If name contains 'inhibitory', 'bias', or specific layer markers
        # In this canonical implementation, we treat all weights as excitatory for scaling
        # and biases as a separate group, but for the E/I ratio enforcement,
        # we focus on the main weight matrices.
        if 'weight' in name and 'inhibitory' not in name:
            excitatory.append(name)
        else:
            inhibitory.append(name)
    
    return excitatory, inhibitory

def calculate_current_activity(model: nn.Module, excitatory_params: List[str], inhibitory_params: List[str]) -> ActivityStats:
    """Calculate current activity levels from parameter magnitudes."""
    total_activity = 0.0
    exc_activity = 0.0
    inh_activity = 0.0

    for name, param in model.named_parameters():
        if name in excitatory_params:
            exc_activity += torch.norm(param).item()
        elif name in inhibitory_params:
            inh_activity += torch.norm(param).item()
    
    total_activity = exc_activity + inh_activity
    current_ratio = exc_activity / (inh_activity + 1e-8)

    return ActivityStats(
        total_activity=total_activity,
        excitatory_activity=exc_activity,
        inhibitory_activity=inh_activity,
        current_ratio=current_ratio
    )

def scale_weights(model: nn.Module, target_ratio: float, decay_rate: float) -> Dict[str, float]:
    """
    Apply synaptic scaling to maintain E/I ratio.
    Formula: new_weight = old_weight * (target_activity / current_activity) ** decay_rate
    """
    excitatory_params, inhibitory_params = identify_excitatory_inhibitory_params(model)
    current_stats = calculate_current_activity(model, excitatory_params, inhibitory_params)
    
    scaling_factors = {}
    
    # Calculate target activity based on desired ratio
    # If current ratio < target, we need to scale up exc or down inh
    # Simplified: Scale excitatory weights to approach target ratio
    if stats.inhibitory_activity > 0:
        target_exc_activity = target_ratio * stats.inhibitory_activity
    else:
        target_exc_activity = target_ratio * 0.1 # Fallback

    # Calculate scaling factor for excitatory weights
    if stats.excitatory_activity > 0:
        scale_factor = (target_exc_activity / stats.excitatory_activity) ** decay_rate
    else:
        scale_factor = 1.0

    # Apply scaling to excitatory parameters
    with torch.no_grad():
        for name, param in model.named_parameters():
            if name in exc_params:
                param.mul_(scale_factor)
                scaling_factors[name] = scale_factor
    
    logger.info(f"Applied scaling factor {scale_factor:.4f} to {len(exc_params)} excitatory parameters")
    return scaling_factors

def enforce_ei_ratio(model: nn.Module, config: HomeostasisConfig) -> Dict[str, float]:
    """Enforce E/I ratio constraint dynamically."""
    return scale_weights(model, config.target_ei_ratio, config.decay_rate)

def apply_ei_balance_constraint(model: nn.Module, config: HomeostasisConfig) -> None:
    """Apply the balance constraint after a training step."""
    scale_weights(model, config.target_ei_ratio, config.decay_rate)

def verify_ei_balance(model: nn.Module, config: HomeostasisConfig) -> bool:
    """Verify if the current E/I ratio is within tolerance."""
    exc_params, inh_params = identify_excitatory_inhibitory_params(model)
    stats = calculate_current_activity(model, exc_params, inh_params)
    
    tolerance = 0.05 # 5% tolerance
    lower_bound = config.target_ei_ratio * (1 - tolerance)
    upper_bound = config.target_ei_ratio * (1 + tolerance)
    
    is_balanced = lower_bound <= stats.current_ratio <= upper_bound
    logger.info(f"E/I Ratio: {stats.current_ratio:.4f} (Target: {config.target_ei_ratio}) - {'OK' if is_balanced else 'VIOLATION'}")
    return is_balanced

class HomeostaticScaler:
    def __init__(self, model: nn.Module, config: HomeostasisConfig):
        self.model = model
        self.config = config
        self.step_count = 0

    def step(self):
        """Perform one step of homeostatic scaling."""
        self.step_count += 1
        if self.step_count % 10 == 0: # Apply every 10 steps
            enforce_ei_ratio(self.model, self.config)
            verify_ei_balance(self.model, self.config)

def apply_scaling_hook(model: nn.Module, config: HomeostasisConfig) -> None:
    """Wrapper to apply scaling hook."""
    scaler = HomeostaticScaler(model, config)
    scaler.step()

def log_gradient_norms(model: nn.Module, step: int) -> None:
    """
    Compute and append gradient norms to data/logs/gradient_norms.json.
    Uses model.register_full_backward_hook to capture gradients.
    """
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    gradient_data = []
    norms_dict = {}

    # We need to capture gradients. Since we can't run backward pass here without data,
    # we assume this function is called AFTER a backward pass has occurred in the training loop.
    # We iterate over parameters that have .grad attribute.
    
    has_gradients = False
    for name, param in model.named_parameters():
        if param.grad is not None:
            has_gradients = True
            norm = torch.norm(param.grad).item()
            norms_dict[name] = norm
        else:
            # If no gradient, record 0 or skip? Task says "compute and append gradient norms"
            # If no grad, norm is 0.
            norms_dict[name] = 0.0

    if not has_gradients:
        logger.warning(f"Step {step}: No gradients found to log.")
    
    entry = {
        "step": step,
        "norms": norms_dict
    }

    # Load existing data if file exists
    if os.path.exists(GRADIENT_LOG_PATH):
        try:
            with open(GRADIENT_LOG_PATH, 'r') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    gradient_data = existing_data
                else:
                    # Handle case where file might have been corrupted or single object
                    gradient_data = [existing_data] if existing_data else []
        except json.JSONDecodeError:
            logger.error(f"Failed to decode {GRADIENT_LOG_PATH}, starting fresh.")
            gradient_data = []
    else:
        gradient_data = []

    # Append new entry
    gradient_data.append(entry)

    # Write back to file
    with open(GRADIENT_LOG_PATH, 'w') as f:
        json.dump(gradient_data, f, indent=2)

    logger.info(f"Logged gradient norms for step {step} to {GRADIENT_LOG_PATH}")

def verify_independence(train_data: Any, test_data: Any) -> bool:
    """Placeholder for independence verification logic if needed here."""
    return True

def main():
    """Main entry point for testing/homeostasis scripts."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Homeostasis module loaded.")
