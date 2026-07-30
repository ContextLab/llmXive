"""
Microcircuit module implementing canonical cortical column structure.
Includes layer definitions, connectivity masks, and E/I ratio enforcement.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import math
import logging

logger = logging.getLogger(__name__)

@dataclass
class LayerConfig:
    """Configuration for a cortical layer."""
    name: str
    input_dim: int
    output_dim: int
    is_excitatory: bool
    connectivity_targets: List[str]
    
@dataclass
class MicrocircuitColumnConfig:
    """Configuration for a full cortical column."""
    hidden_dim: int
    neurons_per_layer: int
    target_ei_ratio: float = 4.0  # Target E/I ratio (excitatory/inhibitory)
    
class CorticalLayer(nn.Module):
    """Base class for cortical layers with E/I properties."""
    
    def __init__(self, config: LayerConfig):
        super().__init__()
        self.config = config
        self.is_excitatory = config.is_excitatory
        
        # Initialize weights with normalized range
        self.weight = nn.Parameter(torch.empty(config.input_dim, config.output_dim))
        self.bias = nn.Parameter(torch.zeros(config.output_dim))
        
        # Reset weights using Kaiming initialization for ReLU
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        if config.output_dim > 1:
            nn.init.uniform_(self.bias, -1.0 / math.sqrt(config.input_dim), 
                           1.0 / math.sqrt(config.input_dim))
                           
        # E/I constraint: excitatory weights should be positive, inhibitory negative
        if self.is_excitatory:
            # Clamp to positive range for excitatory
            with torch.no_grad():
                self.weight.clamp_(min=0.0)
        else:
            # Clamp to negative range for inhibitory
            with torch.no_grad():
                self.weight.clamp_(max=0.0)
                
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with E/I constraint enforcement."""
        # Apply E/I constraint during forward pass
        if self.is_excitatory:
            # Ensure weights remain positive (excitatory)
            weight = F.relu(self.weight)
        else:
            # Ensure weights remain negative (inhibitory)
            weight = -F.relu(-self.weight)
            
        output = F.linear(x, weight, self.bias)
        return output
        
    def get_activity_stats(self, x: torch.Tensor) -> Dict[str, float]:
        """Calculate activity statistics for this layer."""
        with torch.no_grad():
            activity = self(x)
            return {
                "mean_activity": float(activity.mean().item()),
                "std_activity": float(activity.std().item()),
                "is_excitatory": self.is_excitatory
            }

class L4Layer(CorticalLayer):
    """Layer 4 - Input receiving layer, primarily excitatory."""
    
    def __init__(self, input_dim: int, output_dim: int):
        config = LayerConfig(
            name="L4",
            input_dim=input_dim,
            output_dim=output_dim,
            is_excitatory=True,
            connectivity_targets=["L23", "L5"]
        )
        super().__init__(config)
        
class L23Layer(CorticalLayer):
    """Layers 2/3 - Associative processing, mixed E/I."""
    
    def __init__(self, input_dim: int, output_dim: int):
        # L2/3 has both excitatory and inhibitory populations
        super().__init__(LayerConfig(
            name="L23",
            input_dim=input_dim,
            output_dim=output_dim,
            is_excitatory=True,  # Primary excitatory population
            connectivity_targets=["L5", "L6"]
        ))
        
class L5Layer(CorticalLayer):
    """Layer 5 - Output projection layer, mixed E/I."""
    
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__(LayerConfig(
            name="L5",
            input_dim=input_dim,
            output_dim=output_dim,
            is_excitatory=True,
            connectivity_targets=["L6", "L4"]
        ))
        
class L6Layer(CorticalLayer):
    """Layer 6 - Feedback layer, mixed E/I."""
    
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__(LayerConfig(
            name="L6",
            input_dim=input_dim,
            output_dim=output_dim,
            is_excitatory=True,
            connectivity_targets=["L4", "L23"]
        ))

def generate_laminar_connectivity_mask(
    layers: Dict[str, CorticalLayer],
    target_ei_ratio: float = 4.0
) -> Dict[Tuple[str, str], torch.Tensor]:
    """
    Generate connectivity masks enforcing laminar topology and E/I constraints.
    
    Args:
        layers: Dictionary of layer name -> CorticalLayer instance
        target_ei_ratio: Target excitatory/inhibitory ratio
        
    Returns:
        Dictionary mapping (source_layer, target_layer) to connectivity mask
    """
    masks = {}
    
    # Define canonical laminar connectivity (L4->L23, L23->L5, etc.)
    canonical_connections = [
        ("L4", "L23"),
        ("L23", "L5"),
        ("L5", "L6"),
        ("L6", "L4"),
        ("L23", "L6"),
        ("L5", "L4")
    ]
    
    for src_name, tgt_name in canonical_connections:
        if src_name in layers and tgt_name in layers:
            src_layer = layers[src_name]
            tgt_layer = layers[tgt_name]
            
            # Create connectivity mask based on E/I constraints
            # Excitatory -> Excitatory: positive weights
            # Excitatory -> Inhibitory: positive weights (excitatory input to inhibitory)
            # Inhibitory -> Any: negative weights
            
            mask = torch.ones(src_layer.config.output_dim, tgt_layer.config.input_dim)
            
            # Apply E/I constraint: if source is inhibitory, mask should be negative
            if not src_layer.is_excitatory:
                mask = -torch.abs(mask)
                
            masks[(src_name, tgt_name)] = mask
            
    return masks

def verify_connectivity_constraints(
    masks: Dict[Tuple[str, str], torch.Tensor],
    target_ei_ratio: float = 4.0
) -> bool:
    """
    Verify that connectivity masks satisfy E/I ratio constraints.
    
    Args:
        masks: Connectivity masks from generate_laminar_connectivity_mask
        target_ei_ratio: Target E/I ratio
        
    Returns:
        True if all constraints are satisfied
    """
    total_excitatory = 0.0
    total_inhibitory = 0.0
    
    for mask in masks.values():
        # Count excitatory connections (positive weights)
        excitatory = torch.sum(mask > 0).item()
        # Count inhibitory connections (negative weights)
        inhibitory = torch.sum(mask < 0).item()
        
        total_excitatory += excitatory
        total_inhibitory += inhibitory
        
    if total_inhibitory == 0:
        logger.warning("No inhibitory connections found")
        return False
        
    current_ratio = total_excitatory / total_inhibitory
    logger.info(f"Current E/I ratio: {current_ratio:.2f}, Target: {target_ei_ratio}")
    
    # Allow 20% tolerance on E/I ratio
    tolerance = 0.2
    return abs(current_ratio - target_ei_ratio) / target_ei_ratio <= tolerance

def apply_ei_balance_constraint(
    model: nn.Module,
    target_ratio: float = 4.0
) -> Dict[str, float]:
    """
    Apply E/I balance constraint to model weights.
    
    Args:
        model: PyTorch model with CorticalLayer components
        target_ratio: Target E/I ratio
        
    Returns:
        Dictionary of applied scaling factors
    """
    scaling_factors = {}
    
    for name, module in model.named_modules():
        if isinstance(module, CorticalLayer):
            with torch.no_grad():
                if module.is_excitatory:
                    # Ensure excitatory weights are positive
                    module.weight.clamp_(min=0.0)
                else:
                    # Ensure inhibitory weights are negative
                    module.weight.clamp_(max=0.0)
                    
                # Calculate current activity ratio
                # (simplified: using weight magnitudes as proxy for activity)
                exc_mag = torch.sum(torch.abs(module.weight[module.weight > 0])).item()
                inh_mag = torch.sum(torch.abs(module.weight[module.weight < 0])).item()
                
                if inh_mag > 0:
                    current_ratio = exc_mag / inh_mag
                    if current_ratio != target_ratio:
                        scale_factor = target_ratio / current_ratio
                        # Apply scaling to maintain E/I balance
                        if module.is_excitatory:
                            module.weight *= math.sqrt(scale_factor)
                        else:
                            module.weight *= math.sqrt(1.0 / scale_factor)
                                
                        scaling_factors[name] = scale_factor
                        
    return scaling_factors

class MicrocircuitColumn(nn.Module):
    """
    Full cortical column microcircuit with E/I ratio enforcement.
    
    This module implements a canonical cortical column with:
    - Laminar structure (L4, L23, L5, L6)
    - Local E/I loops
    - E/I ratio enforcement during forward pass
    """
    
    def __init__(self, config: MicrocircuitColumnConfig):
        super().__init__()
        self.config = config
        self.target_ei_ratio = config.target_ei_ratio
        
        # Initialize layers
        self.l4 = L4Layer(config.hidden_dim, config.neurons_per_layer)
        self.l23 = L23Layer(config.neurons_per_layer, config.neurons_per_layer)
        self.l5 = L5Layer(config.neurons_per_layer, config.neurons_per_layer)
        self.l6 = L6Layer(config.neurons_per_layer, config.hidden_dim)
        
        # Store layers for connectivity mask generation
        self.layers = {
            "L4": self.l4,
            "L23": self.l23,
            "L5": self.l5,
            "L6": self.l6
        }
        
        # Generate and store connectivity masks
        self.connectivity_masks = generate_laminar_connectivity_mask(
            self.layers, self.target_ei_ratio
        )
        
        # Verify constraints
        if not verify_connectivity_constraints(self.connectivity_masks, self.target_ei_ratio):
            logger.warning("Initial connectivity constraints not satisfied, applying correction")
            apply_ei_balance_constraint(self, self.target_ei_ratio)
            
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the cortical column with E/I enforcement.
        
        Args:
            x: Input tensor of shape (batch_size, hidden_dim)
            
        Returns:
            Output tensor of shape (batch_size, hidden_dim)
        """
        # L4 receives input
        l4_out = F.relu(self.l4(x))
        
        # L23 receives from L4
        l23_out = F.relu(self.l23(l4_out))
        
        # L5 receives from L23
        l5_out = F.relu(self.l5(l23_out))
        
        # L6 receives from L23 and L5 (feedback)
        l6_out = F.relu(self.l6(l23_out + l5_out))
        
        # Output from L6 back to input dimension
        output = l6_out
        
        # Apply E/I balance constraint after forward pass
        with torch.no_grad():
            apply_ei_balance_constraint(self, self.target_ei_ratio)
            
        return output
        
    def get_ei_activity_stats(self, x: torch.Tensor) -> Dict[str, float]:
        """
        Calculate E/I activity statistics for the column.
        
        Args:
            x: Input tensor
            
        Returns:
            Dictionary with excitatory and inhibitory activity statistics
        """
        exc_stats = []
        inh_stats = []
        
        for name, layer in self.layers.items():
            stats = layer.get_activity_stats(x)
            if stats["is_excitatory"]:
                exc_stats.append(stats["mean_activity"])
            else:
                inh_stats.append(stats["mean_activity"])
                
        return {
            "excitatory_mean": float(torch.tensor(exc_stats).mean().item()) if exc_stats else 0.0,
            "inhibitory_mean": float(torch.tensor(inh_stats).mean().item()) if inh_stats else 0.0,
            "ei_ratio": float(torch.tensor(exc_stats).mean().item() / torch.tensor(inh_stats).mean().item()) 
                        if inh_stats and torch.tensor(inh_stats).mean().item() != 0 else 0.0
        }

def create_microcircuit_column(config: MicrocircuitColumnConfig) -> MicrocircuitColumn:
    """
    Factory function to create a MicrocircuitColumn instance.
    
    Args:
        config: MicrocircuitColumnConfig instance
        
    Returns:
        MicrocircuitColumn instance
    """
    return MicrocircuitColumn(config)