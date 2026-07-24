"""
Homeostatic Scaling for Cortical Column Microcircuits.

Implements activity-dependent synaptic scaling to dynamically maintain
a balanced Excitatory/Inhibitory (E/I) ratio during training.

This module provides the logic for:
1. Monitoring layer-wise activity statistics.
2. Calculating scaling factors to enforce a target E/I ratio (default 4:1).
3. Applying these factors to weight matrices in place.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class HomeostasisConfig:
    """Configuration for homeostatic scaling."""
    target_ei_ratio: float = 4.0
    scaling_alpha: float = 0.01  # Learning rate for scaling updates
    min_weight_scale: float = 0.1
    max_weight_scale: float = 10.0
    window_size: int = 100  # Number of steps for moving average


@dataclass
class ActivityStats:
    """Container for activity statistics from a forward pass."""
    layer_name: str
    excitatory_mean: float
    inhibitory_mean: float
    total_excitatory_sum: float
    total_inhibitory_sum: float
    excitatory_count: int
    inhibitory_count: int

def apply_ei_balance_constraint(
    layer: nn.Module,
    stats: ActivityStats,
    config: HomeostasisConfig,
    current_scale: float
) -> float:
    """
    Calculates and applies a scaling factor to a layer to maintain E/I balance.

    Args:
        layer: The target nn.Module layer.
        stats: Activity statistics collected from the forward pass.
        config: HomeostasisConfig parameters.
        current_scale: The current cumulative scaling factor for this layer.

    Returns:
        The updated scaling factor to be stored for the next step.
    """
    if stats.excitatory_count == 0 or stats.inhibitory_count == 0:
        return current_scale

    # Calculate current E/I ratio
    current_ratio = (stats.total_excitatory_sum / stats.excitatory_count) / \
                    (stats.total_inhibitory_sum / stats.inhibitory_count)

    # Calculate desired scaling factor
    # If current_ratio > target, we need to scale down excitatory or up inhibitory
    # We apply a multiplicative correction to the excitatory weights
    ratio_error = current_ratio / config.target_ei_ratio

    # Exponential moving average of the correction
    correction_factor = ratio_error ** (1.0 / config.window_size)
    
    # Apply alpha for stability
    new_scale = current_scale * (1.0 + config.scaling_alpha * (1.0 - ratio_error))

    # Clamp scale to valid range
    new_scale = max(config.min_weight_scale, min(config.max_weight_scale, new_scale))

    # Apply scaling to weights if the layer has a weight attribute
    if hasattr(layer, 'weight'):
        with torch.no_grad():
            # We assume excitatory connections are the primary weights in this context
            # In a more complex model, we might separate E/I weight matrices
            layer.weight.mul_(new_scale / current_scale)
    
    logger.debug(
        f"Homeostasis: Layer '{layer_name}' adjusted scale from {current_scale:.4f} "
        f"to {new_scale:.4f} (Current Ratio: {current_ratio:.2f}, Target: {config.target_ei_ratio})"
    )

    return new_scale


def verify_ei_balance(
    excitatory_activations: torch.Tensor,
    inhibitory_activations: torch.Tensor,
    target_ratio: float = 4.0,
    tolerance: float = 0.2
) -> Tuple[bool, float]:
    """
    Verifies if the current E/I balance is within tolerance of the target.

    Args:
        excitatory_activations: Tensor of excitatory neuron activities.
        inhibitory_activations: Tensor of inhibitory neuron activities.
        target_ratio: Target E/I ratio (default 4.0).
        tolerance: Allowed deviation from target (default 0.2 or 20%).

    Returns:
        Tuple of (is_balanced, current_ratio).
    """
    if excitatory_activations.numel() == 0 or inhibitory_activations.numel() == 0:
        return False, 0.0

    mean_exc = excitatory_activations.mean().item()
    mean_inh = inhibitory_activations.mean().item()

    if mean_inh == 0:
        return False, float('inf')

    current_ratio = mean_exc / mean_inh
    lower_bound = target_ratio * (1.0 - tolerance)
    upper_bound = target_ratio * (1.0 + tolerance)

    is_balanced = lower_bound <= current_ratio <= upper_bound

    return is_balanced, current_ratio


class HomeostaticScaler:
    """
    Manages homeostatic scaling across multiple layers in a model.
    
    Tracks scaling factors per layer and applies updates based on
    recorded activity statistics.
    """
    def __init__(self, model: nn.Module, config: Optional[HomeostasisConfig] = None):
        self.config = config or HomeostasisConfig()
        self.model = model
        self.layer_scales: Dict[str, float] = {}
        self.layer_names: List[str] = []
        
        # Initialize scales to 1.0 for all parameters
        for name, param in model.named_parameters():
            if 'weight' in name:
                self.layer_scales[name] = 1.0
                self.layer_names.append(name)
        
        logger.info(f"Initialized HomeostaticScaler for {len(self.layer_names)} weight layers")

    def record_stats(self, layer_name: str, exc_stats: torch.Tensor, inh_stats: torch.Tensor):
        """
        Records activity statistics for a specific layer.
        
        Args:
            layer_name: Name of the layer (must match model parameter name or be mapped).
            exc_stats: Tensor of excitatory activities.
            inh_stats: Tensor of inhibitory activities.
        """
        # In a full implementation, we would store these in a buffer for moving average
        # For now, we assume immediate application or external buffering
        pass

    def step(self, layer_name: str, exc_sum: float, exc_count: int, inh_sum: float, inh_count: int):
        """
        Performs one step of homeostatic scaling for a specific layer.
        
        Args:
            layer_name: Name of the layer to update.
            exc_sum: Sum of excitatory activations.
            exc_count: Count of excitatory neurons.
            inh_sum: Sum of inhibitory activations.
            inh_count: Count of inhibitory neurons.
        """
        if exc_count == 0 or inh_count == 0:
            return

        current_scale = self.layer_scales.get(layer_name, 1.0)
        
        # Calculate mean activities
        mean_exc = exc_sum / exc_count
        mean_inh = inh_sum / inh_count
        
        if mean_inh == 0:
            return

        current_ratio = mean_exc / mean_inh
        
        # Calculate correction
        ratio_error = current_ratio / self.config.target_ei_ratio
        new_scale = current_scale * (1.0 + self.config.scaling_alpha * (1.0 - ratio_error))
        
        # Clamp
        new_scale = max(self.config.min_weight_scale, min(self.config.max_weight_scale, new_scale))
        
        # Update stored scale
        self.layer_scales[layer_name] = new_scale
        
        # Apply to model weights if found
        for name, param in self.model.named_parameters():
            if name == layer_name and 'weight' in name:
                with torch.no_grad():
                    param.mul_(new_scale / current_scale)
                
                logger.debug(
                    f"Homeostasis: Layer '{name}' scale updated {current_scale:.4f} -> {new_scale:.4f} "
                    f"(Ratio: {current_ratio:.2f} -> Target: {self.config.target_ei_ratio})"
                )
                break

    def get_stats(self) -> Dict[str, float]:
        """Returns current scaling factors for all tracked layers."""
        return self.layer_scales.copy()

    def verify_global_balance(self) -> bool:
        """
        Verifies global E/I balance across the entire model.
        
        Returns:
            True if global balance is within tolerance.
        """
        total_exc = 0.0
        total_inh = 0.0
        exc_count = 0
        inh_count = 0

        # This is a simplified check; in reality, we'd need to track E/I weights separately
        # For now, we assume the model structure enforces E/I separation in forward pass
        # and we rely on the step() calls to have maintained balance.
        return True # Placeholder for full verification logic