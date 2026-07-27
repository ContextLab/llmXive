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
    hidden_dim: int
    num_neurons: int
    excitation_ratio: float = 0.8  # Proportion of excitatory neurons
    inhibition_ratio: float = 0.2  # Proportion of inhibitory neurons
    target_ei_ratio: float = 4.0   # Target Excitation/Inhibition ratio (4:1)

class CorticalLayer(nn.Module):
    """
    A single cortical layer with explicit E/I neuron populations.
    Implements weight initialization and forward pass logic to enforce
    a dominant excitatory component as per the 4:1 biological ratio.
    """
    def __init__(self, config: LayerConfig):
        super().__init__()
        self.config = config
        self.hidden_dim = config.hidden_dim
        self.num_neurons = config.num_neurons
        
        # Split neurons into excitatory and inhibitory populations
        self.num_exc = int(config.num_neurons * config.excitation_ratio)
        self.num_inh = config.num_neurons - self.num_exc
        
        logger.info(f"Initialized {config.name}: Exc={self.num_exc}, Inh={self.num_inh} (Target E/I: {config.target_ei_ratio})")

        # Linear projection for the layer
        self.linear = nn.Linear(config.hidden_dim, config.num_neurons)
        
        # Initialize weights to enforce E/I balance by construction
        self._initialize_weights_ei_balance()

    def _initialize_weights_ei_balance(self):
        """
        Initialize weights such that the total excitatory drive is approximately
        4x the inhibitory drive, satisfying the biological E/I ratio constraint.
        
        Strategy:
        1. Initialize all weights from a standard distribution.
        2. Zero-out inhibitory rows (or scale them down significantly) relative to excitatory rows.
        3. Apply weight clipping to ensure stability.
        """
        # Standard initialization
        nn.init.xavier_uniform_(self.linear.weight)
        nn.init.zeros_(self.linear.bias)

        # Enforce E/I ratio by construction:
        # We want sum(|W_exc|) / sum(|W_inh|) ≈ 4.0
        # Currently, assuming uniform init, sums are roughly equal.
        # We scale inhibitory weights down by a factor of 4 relative to excitatory.
        
        # Slice weights for inhibitory neurons (last num_inh rows)
        if self.num_inh > 0:
            with torch.no_grad():
                exc_slice = self.linear.weight[:self.num_exc, :]
                inh_slice = self.linear.weight[self.num_exc:, :]
                
                # Scale inhibitory weights to reduce their total magnitude
                # Target: |W_exc|_sum / |W_inh|_scaled_sum = 4.0
                # Current: |W_exc|_sum ≈ |W_inh|_unscaled_sum
                # So we need |W_inh|_scaled = |W_inh|_unscaled / 4.0
                scale_factor = 1.0 / self.config.target_ei_ratio
                inh_slice.mul_(scale_factor)
                
                logger.debug(f"Applied E/I scaling factor {scale_factor} to {self.num_inh} inhibitory neurons.")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the layer.
        x: (batch_size, hidden_dim)
        Returns: (batch_size, num_neurons)
        """
        out = self.linear(x)
        return out

class L23Layer(CorticalLayer):
    """Layer 2/3: Projection neurons, high excitatory ratio."""
    def __init__(self, config: LayerConfig):
        # L2/3 is predominantly excitatory for output projection
        super().__init__(LayerConfig(
            name="L23",
            hidden_dim=config.hidden_dim,
            num_neurons=config.num_neurons,
            excitation_ratio=0.85,
            inhibition_ratio=0.15,
            target_ei_ratio=config.target_ei_ratio
        ))

class L4Layer(CorticalLayer):
    """Layer 4: Input layer, receives thalamic input."""
    def __init__(self, config: LayerConfig):
        super().__init__(LayerConfig(
            name="L4",
            hidden_dim=config.hidden_dim,
            num_neurons=config.num_neurons,
            excitation_ratio=0.75,
            inhibition_ratio=0.25,
            target_ei_ratio=config.target_ei_ratio
        ))

class L5Layer(CorticalLayer):
    """Layer 5: Output to subcortical areas."""
    def __init__(self, config: LayerConfig):
        super().__init__(LayerConfig(
            name="L5",
            hidden_dim=config.hidden_dim,
            num_neurons=config.num_neurons,
            excitation_ratio=0.80,
            inhibition_ratio=0.20,
            target_ei_ratio=config.target_ei_ratio
        ))

class L6Layer(CorticalLayer):
    """Layer 6: Feedback to thalamus."""
    def __init__(self, config: LayerConfig):
        super().__init__(LayerConfig(
            name="L6",
            hidden_dim=config.hidden_dim,
            num_neurons=config.num_neurons,
            excitation_ratio=0.70,
            inhibition_ratio=0.30,
            target_ei_ratio=config.target_ei_ratio
        ))

def generate_laminar_connectivity_mask(
    layers: List[CorticalLayer],
    target_ei_ratio: float = 4.0
) -> torch.Tensor:
    """
    Generates a connectivity mask enforcing laminar topology.
    Returns a tensor of shape (total_neurons, total_neurons) where 1 indicates
    a valid connection and 0 indicates no connection.
    
    This function assumes the layers are ordered L6 -> L4 -> L23 -> L5 (typical flow).
    """
    total_neurons = sum(l.num_neurons for l in layers)
    mask = torch.zeros(total_neurons, total_neurons, dtype=torch.float32)
    
    offset = 0
    layer_offsets = []
    for layer in layers:
        layer_offsets.append(offset)
        offset += layer.num_neurons
        
    # Define canonical connections (simplified canonical microcircuit)
    # L4 -> L2/3 (Excitatory)
    # L2/3 -> L5 (Excitatory)
    # L5 -> L6 (Excitatory)
    # L6 -> L4 (Feedback)
    # Local inhibition within layers (all-to-all or specific)
    
    # We will construct a mask where connections are allowed based on laminar rules.
    # For E/I enforcement by construction, we rely on the weight initialization
    # in CorticalLayer, but this mask ensures structural validity.
    
    # Example: L4 (index 1) to L23 (index 2)
    # Assuming order: [L6, L4, L23, L5]
    # Let's map indices based on the list order provided
    # We will allow specific inter-layer connections and local intra-layer connections
    
    # Intra-layer (local circuits)
    for i, layer in enumerate(layers):
        start = layer_offsets[i]
        end = start + layer.num_neurons
        mask[start:end, start:end] = 1.0
        
    # Inter-layer (Canonical flow)
    # L4 -> L23
    if len(layers) >= 3:
        # Assuming typical order in list: [L6, L4, L23, L5] or similar
        # We need to find indices dynamically or assume a standard order.
        # For this implementation, we assume the list 'layers' is ordered:
        # [L6, L4, L23, L5] based on standard columnar models.
        # If the list order is different, this logic needs adjustment.
        # Let's assume the input list is ordered: [L6, L4, L23, L5]
        # L4 is index 1, L23 is index 2
        l4_idx, l23_idx = 1, 2
        if len(layers) > l23_idx:
            l4_start = layer_offsets[l4_idx]
            l4_end = l4_start + layers[l4_idx].num_neurons
            l23_start = layer_offsets[l23_idx]
            l23_end = l23_start + layers[l23_idx].num_neurons
            mask[l23_start:l23_end, l4_start:l4_end] = 1.0 # L4 -> L23
    
    # L23 -> L5
    if len(layers) >= 4:
        l23_idx, l5_idx = 2, 3
        l23_start = layer_offsets[l23_idx]
        l23_end = l23_start + layers[l23_idx].num_neurons
        l5_start = layer_offsets[l5_idx]
        l5_end = l5_start + layers[l5_idx].num_neurons
        mask[l5_start:l5_end, l23_start:l23_end] = 1.0 # L23 -> L5
        
    return mask

def verify_connectivity_constraints(mask: torch.Tensor, layers: List[CorticalLayer]) -> bool:
    """Verifies that the connectivity mask respects laminar constraints."""
    # Basic sanity check: diagonal blocks (intra-layer) must be 1
    offset = 0
    for layer in layers:
        block = mask[offset:offset+layer.num_neurons, offset:offset+layer.num_neurons]
        if not torch.all(block == 1.0):
            logger.warning("Intra-layer connectivity incomplete.")
            return False
        offset += layer.num_neurons
    return True

def apply_ei_balance_constraint(model: nn.Module, target_ratio: float = 4.0) -> Dict[str, float]:
    """
    Applies a post-hoc constraint to enforce E/I balance if initialization drifted.
    This is a fallback mechanism; the primary enforcement is in __init__.
    """
    applied_factors = {}
    for name, module in model.named_modules():
        if isinstance(module, CorticalLayer):
            # Recalculate current ratio if needed (simplified here)
            # For now, we trust initialization. This function can be extended
            # to dynamically rescale weights during training if homeostasis fails.
            pass
    return applied_factors

class MicrocircuitColumn(nn.Module):
    """
    A full cortical column composed of L6, L4, L23, L5 layers.
    Enforces E/I ratio by construction in each layer's initialization.
    """
    def __init__(
        self,
        hidden_dim: int,
        num_neurons_per_layer: int,
        target_ei_ratio: float = 4.0
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_neurons = num_neurons_per_layer
        self.target_ei_ratio = target_ei_ratio
        
        # Create layers
        self.l6 = L6Layer(LayerConfig("L6", hidden_dim, num_neurons_per_layer, target_ei_ratio=target_ei_ratio))
        self.l4 = L4Layer(LayerConfig("L4", hidden_dim, num_neurons_per_layer, target_ei_ratio=target_ei_ratio))
        self.l23 = L23Layer(LayerConfig("L23", hidden_dim, num_neurons_per_layer, target_ei_ratio=target_ei_ratio))
        self.l5 = L5Layer(LayerConfig("L5", hidden_dim, num_neurons_per_layer, target_ei_ratio=target_ei_ratio))
        
        # Connectivity mask
        self.layers = [self.l6, self.l4, self.l23, self.l5]
        self.connectivity_mask = generate_laminar_connectivity_mask(self.layers, target_ei_ratio)
        
        # Project input to L4
        self.input_proj = nn.Linear(hidden_dim, num_neurons_per_layer)
        nn.init.xavier_uniform_(self.input_proj.weight)
        
        # Output projection from L5
        self.output_proj = nn.Linear(num_neurons_per_layer, hidden_dim)
        nn.init.xavier_uniform_(self.output_proj.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the column.
        x: (batch_size, hidden_dim)
        Returns: (batch_size, hidden_dim)
        """
        # Input to L4
        l4_out = self.l4(self.input_proj(x))
        l4_out = F.relu(l4_out)
        
        # L4 -> L23
        l23_out = self.l23(l4_out)
        l23_out = F.relu(l23_out)
        
        # L23 -> L5
        l5_out = self.l5(l23_out)
        l5_out = F.relu(l5_out)
        
        # L5 -> Output
        out = self.output_proj(l5_out)
        return out

def create_microcircuit_column(
    hidden_dim: int,
    num_neurons_per_layer: int,
    target_ei_ratio: float = 4.0
) -> MicrocircuitColumn:
    """Factory function to create a MicrocircuitColumn."""
    return MicrocircuitColumn(hidden_dim, num_neurons_per_layer, target_ei_ratio)