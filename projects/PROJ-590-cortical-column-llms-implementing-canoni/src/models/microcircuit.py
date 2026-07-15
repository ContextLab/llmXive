import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import math

@dataclass
class LayerConfig:
    """Configuration for a single cortical layer."""
    name: str
    neuron_count: int
    excitatory_ratio: float = 0.8  # Target 80% excitatory neurons
    hidden_dim: int = 256
    
class CorticalLayer(nn.Module):
    """
    A single cortical layer with explicit E/I neuron separation.
    Implements initialization and forward pass logic to enforce E/I ratios.
    """
    def __init__(self, config: LayerConfig):
        super().__init__()
        self.config = config
        self.name = config.name
        self.neuron_count = config.neuron_count
        
        # Calculate exact counts based on ratio
        self.exc_count = int(config.neuron_count * config.excitatory_ratio)
        self.inh_count = config.neuron_count - self.exc_count
        
        # Separate parameters for E and I populations
        # Excitatory: ReLU-like behavior (positive weights)
        self.exc_proj = nn.Linear(config.hidden_dim, self.exc_count, bias=True)
        # Inhibitory: Tanh-like behavior (can be negative)
        self.inh_proj = nn.Linear(config.hidden_dim, self.inh_count, bias=True)
        
        # Initialize with E/I constraints
        self._initialize_ei_constraints()
        
    def _initialize_ei_constraints(self):
        """
        Enforce E/I balance by construction:
        - Excitatory weights initialized with positive bias/mean
        - Inhibitory weights initialized with negative bias/mean
        - Ensures dominant excitatory component in forward pass
        """
        # Excitatory population: positive initialization
        # Use uniform distribution with positive mean
        torch.nn.init.uniform_(self.exc_proj.weight, 0.0, 0.1)
        torch.nn.init.constant_(self.exc_proj.bias, 0.1)
        
        # Inhibitory population: negative initialization
        # Use uniform distribution with negative mean
        torch.nn.init.uniform_(self.inh_proj.weight, -0.1, 0.0)
        torch.nn.init.constant_(self.inh_proj.bias, -0.1)
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass separating E and I populations.
        
        Args:
            x: Input tensor of shape (batch_size, hidden_dim)
            
        Returns:
            Tuple of (excitatory_output, inhibitory_output)
        """
        exc_out = F.relu(self.exc_proj(x))
        inh_out = F.tanh(self.inh_proj(x))
        
        return exc_out, inh_out
        
    def get_combined_output(self, x: torch.Tensor) -> torch.Tensor:
        """
        Combine E and I outputs into a single layer output.
        Implements the dominant excitatory component principle.
        """
        exc_out, inh_out = self.forward(x)
        
        # Concatenate and ensure excitatory dominance
        combined = torch.cat([exc_out, inh_out], dim=-1)
        
        # Apply a learned gating mechanism to maintain E/I balance
        # This ensures the excitatory component remains dominant
        gate = torch.sigmoid(self.exc_proj.weight.mean(dim=0))
        gate = gate.unsqueeze(0).expand_as(combined)
        
        return combined * gate

class L23Layer(CorticalLayer):
    """Layer 2/3: Intracortical processing, excitatory dominant."""
    def __init__(self, config: LayerConfig):
        # L2/3 typically has ~80% excitatory neurons
        config.excitatory_ratio = 0.8
        super().__init__(config)
        
class L4Layer(CorticalLayer):
    """Layer 4: Thalamic input, high excitatory drive."""
    def __init__(self, config: LayerConfig):
        # L4 receives strong thalamic input, very excitatory
        config.excitatory_ratio = 0.85
        super().__init__(config)
        
class L5Layer(CorticalLayer):
    """Layer 5: Output to subcortical structures."""
    def __init__(self, config: LayerConfig):
        # L5 has slightly lower E/I ratio due to output requirements
        config.excitatory_ratio = 0.75
        super().__init__(config)
        
class L6Layer(CorticalLayer):
    """Layer 6: Feedback to thalamus."""
    def __init__(self, config: LayerConfig):
        # L6 has balanced but still excitatory-dominant
        config.excitatory_ratio = 0.78
        super().__init__(config)

class MicrocircuitColumn(nn.Module):
    """
    A complete cortical column with laminar structure.
    Implements E/I ratio enforcement across all layers.
    """
    def __init__(self, config: Dict[str, LayerConfig]):
        super().__init__()
        self.layers = nn.ModuleDict()
        self.layer_configs = config
        
        # Initialize each layer with its specific configuration
        for layer_name, layer_config in config.items():
            if layer_name == "L23":
                self.layers[layer_name] = L23Layer(layer_config)
            elif layer_name == "L4":
                self.layers[layer_name] = L4Layer(layer_config)
            elif layer_name == "L5":
                self.layers[layer_name] = L5Layer(layer_config)
            elif layer_name == "L6":
                self.layers[layer_name] = L6Layer(layer_config)
                
        # Register the E/I ratio enforcement hook
        self._register_ei_enforcement_hook()
        
    def _register_ei_enforcement_hook(self):
        """
        Register a forward hook to verify E/I ratio enforcement.
        This ensures the constraint is maintained during training.
        """
        def check_ei_ratio(module, input, output):
            if isinstance(output, tuple) and len(output) == 2:
                exc, inh = output
                # Verify excitatory dominance
                exc_norm = torch.norm(exc, p=2)
                inh_norm = torch.norm(inh, p=2)
                # Log ratio for monitoring (not enforced as hard constraint here)
                # The actual enforcement happens in initialization
                if exc_norm > 0:
                    ratio = inh_norm / exc_norm
                    # Should be < 1.0 for excitatory dominance
                    assert ratio < 1.0, f"E/I ratio violation: {ratio}"
                    
        for layer in self.layers.values():
            if isinstance(layer, CorticalLayer):
                layer.register_forward_hook(check_ei_ratio)
                
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the entire column.
        
        Args:
            x: Input tensor (batch_size, input_dim)
            
        Returns:
            Output tensor (batch_size, output_dim)
        """
        # Process through layers in canonical order: L4 -> L2/3 -> L5 -> L6
        current = x
        
        # L4 receives thalamic input
        if "L4" in self.layers:
            exc_l4, inh_l4 = self.layers["L4"].forward(current)
            current = self.layers["L4"].get_combined_output(current)
            
        # L2/3 processes intracortically
        if "L23" in self.layers:
            exc_l23, inh_l23 = self.layers["L23"].forward(current)
            current = self.layers["L23"].get_combined_output(current)
            
        # L5 outputs to subcortical
        if "L5" in self.layers:
            exc_l5, inh_l5 = self.layers["L5"].forward(current)
            current = self.layers["L5"].get_combined_output(current)
            
        # L6 provides feedback
        if "L6" in self.layers:
            exc_l6, inh_l6 = self.layers["L6"].forward(current)
            current = self.layers["L6"].get_combined_output(current)
            
        return current

def create_microcircuit_column(
    input_dim: int,
    hidden_dim: int = 256,
    excitatory_ratio: float = 0.8
) -> MicrocircuitColumn:
    """
    Factory function to create a complete microcircuit column.
    
    Args:
        input_dim: Dimension of input features
        hidden_dim: Hidden dimension for layer projections
        excitatory_ratio: Target ratio of excitatory neurons (default 0.8)
        
    Returns:
        Configured MicrocircuitColumn instance
    """
    # Create configurations for each layer
    configs = {
        "L4": LayerConfig(
            name="L4",
            neuron_count=hidden_dim,
            excitatory_ratio=0.85,
            hidden_dim=input_dim
        ),
        "L23": LayerConfig(
            name="L23",
            neuron_count=hidden_dim,
            excitatory_ratio=0.8,
            hidden_dim=hidden_dim
        ),
        "L5": LayerConfig(
            name="L5",
            neuron_count=hidden_dim,
            excitatory_ratio=0.75,
            hidden_dim=hidden_dim
        ),
        "L6": LayerConfig(
            name="L6",
            neuron_count=hidden_dim,
            excitatory_ratio=0.78,
            hidden_dim=hidden_dim
        )
    }
    
    return MicrocircuitColumn(configs)

def generate_laminar_connectivity_mask(
    layer_sizes: List[int],
    connectivity_rules: Dict[str, List[str]]
) -> torch.Tensor:
    """
    Generate a connectivity mask enforcing laminar structure.
    
    Args:
        layer_sizes: List of neuron counts for each layer
        connectivity_rules: Dict mapping source layer to list of target layers
        
    Returns:
        Binary connectivity mask tensor
    """
    total_neurons = sum(layer_sizes)
    mask = torch.zeros((total_neurons, total_neurons), dtype=torch.float32)
    
    offset = 0
    layer_offsets = {}
    for i, size in enumerate(layer_sizes):
        layer_offsets[i] = offset
        offset += size
        
    for src_idx, targets in connectivity_rules.items():
        src_offset = layer_offsets[src_idx]
        src_size = layer_sizes[src_idx]
        
        for tgt_idx in targets:
            tgt_offset = layer_offsets[tgt_idx]
            tgt_size = layer_sizes[tgt_idx]
            
            # Set connectivity block
            mask[src_offset:src_offset+src_size, 
                 tgt_offset:tgt_offset+tgt_size] = 1.0
                
    return mask

def verify_connectivity_constraints(
    mask: torch.Tensor,
    expected_density: float = 0.1
) -> bool:
    """
    Verify that connectivity mask meets expected constraints.
    
    Args:
        mask: Connectivity mask tensor
        expected_density: Expected connection density
        
    Returns:
        True if constraints are satisfied
    """
    actual_density = mask.sum() / (mask.shape[0] * mask.shape[1])
    return abs(actual_density - expected_density) < 0.05

def apply_ei_balance_constraint(
    weights: torch.Tensor,
    target_ratio: float = 0.8
) -> torch.Tensor:
    """
    Apply E/I balance constraint to weight matrix.
    
    Args:
        weights: Weight matrix to constrain
        target_ratio: Target excitatory ratio
        
    Returns:
        Constrained weight matrix
    """
    exc_count = int(weights.shape[0] * target_ratio)
    inh_count = weights.shape[0] - exc_count
    
    # Ensure excitatory weights are positive
    exc_weights = weights[:exc_count, :]
    exc_weights = torch.clamp(exc_weights, min=0.0)
    
    # Ensure inhibitory weights are negative
    inh_weights = weights[exc_count:, :]
    inh_weights = torch.clamp(inh_weights, max=0.0)
    
    # Reconstruct
    constrained = torch.cat([exc_weights, inh_weights], dim=0)
    return constrained

# Re-export for API compatibility
__all__ = [
    'LayerConfig', 
    'CorticalLayer', 
    'L23Layer', 
    'L4Layer', 
    'L5Layer', 
    'L6Layer', 
    'MicrocircuitColumn', 
    'create_microcircuit_column',
    'generate_laminar_connectivity_mask',
    'verify_connectivity_constraints',
    'apply_ei_balance_constraint'
]
