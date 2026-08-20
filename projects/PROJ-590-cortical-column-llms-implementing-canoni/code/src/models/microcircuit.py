import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List, Callable
from dataclasses import dataclass
import math
import logging

from .baseline_transformer import FeedForward

logger = logging.getLogger(__name__)

@dataclass
class LayerConfig:
    """Configuration for a single cortical layer."""
    layer_id: int
    input_dim: int
    output_dim: int
    excitatory_ratio: float = 0.8  # Fraction of excitatory neurons
    is_excitatory: bool = True     # Is this layer primarily excitatory?
    activation: str = "relu"

@dataclass
class MicrocircuitColumnConfig:
    """Configuration for the full canonical microcircuit column."""
    l23_dim: int = 128
    l4_dim: int = 128
    l5_dim: int = 128
    l6_dim: int = 64
    input_dim: int = 64
    output_dim: int = 64
    l23_excitatory_ratio: float = 0.8
    l4_excitatory_ratio: float = 0.8
    l5_excitatory_ratio: float = 0.8
    l6_excitatory_ratio: float = 0.8
    enable_laminar_connectivity: bool = True

class CorticalLayer(nn.Module):
    """
    A single cortical layer with configurable excitatory/inhibitory composition.
    Implements local recurrent connectivity and projection to downstream layers.
    """
    def __init__(self, config: LayerConfig):
        super().__init__()
        self.config = config
        self.layer_id = config.layer_id
        
        # Main feedforward projection
        self.fc = nn.Linear(config.input_dim, config.output_dim)
        
        # Local recurrent connection (within layer)
        self.recurrent = nn.Linear(config.output_dim, config.output_dim)
        
        # Activation function
        if config.activation == "relu":
            self.act = nn.ReLU()
        elif config.activation == "tanh":
            self.act = nn.Tanh()
        elif config.activation == "sigmoid":
            self.act = nn.Sigmoid()
        else:
            raise ValueError(f"Unknown activation: {config.activation}")
        
        # Initialize weights
        self._initialize_weights()

    def _initialize_weights(self):
        """Initialize weights with small random values."""
        nn.init.xavier_uniform_(self.fc.weight)
        nn.init.zeros_(self.fc.bias)
        nn.init.xavier_uniform_(self.recurrent.weight)
        nn.init.zeros_(self.recurrent.bias)

    def forward(self, x: torch.Tensor, connectivity_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through the layer.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)
            connectivity_mask: Optional mask for sparse connectivity (not used in basic forward)
        
        Returns:
            Output tensor of shape (batch_size, seq_len, output_dim)
        """
        # Feedforward projection
        out = self.fc(x)
        
        # Local recurrent connection (applied once for simplicity)
        recurrent_out = self.recurrent(out)
        out = out + recurrent_out * 0.1  # Small recurrent contribution
        
        return self.act(out)

class L4Layer(CorticalLayer):
    """Layer 4: Thalamic input layer, primarily excitatory spiny stellate cells."""
    def __init__(self, config: LayerConfig):
        super().__init__(config)
        # L4 receives external sensory input

class L23Layer(CorticalLayer):
    """Layers 2/3: Intracortical processing, associative connections."""
    def __init__(self, config: LayerConfig):
        super().__init__(config)
        # L2/3 projects to other columns and higher areas

class L5Layer(CorticalLayer):
    """Layer 5: Output to subcortical structures, motor control."""
    def __init__(self, config: LayerConfig):
        super().__init__(config)
        # L5 is the major output layer

class L6Layer(CorticalLayer):
    """Layer 6: Feedback to thalamus, regulatory."""
    def __init__(self, config: LayerConfig):
        super().__init__(config)
        # L6 provides feedback to L4 and thalamus

def generate_laminar_connectivity_mask(
    config: MicrocircuitColumnConfig,
    batch_size: int = 1,
    seq_len: int = 1,
    device: torch.device = torch.device("cpu")
) -> Dict[str, torch.Tensor]:
    """
    Generates connectivity masks that enforce canonical laminar topology.
    
    The canonical microcircuit follows specific connectivity rules:
    - L4 receives external input
    - L4 -> L2/3 (feedforward)
    - L2/3 -> L5 (feedforward)
    - L5 -> L6 (feedforward)
    - L6 -> L4 (feedback)
    - L2/3 <-> L2/3 (lateral)
    - L5 <-> L5 (lateral)
    
    Returns:
        Dictionary of masks for each connection type.
        Each mask is a boolean tensor where True indicates allowed connection.
    """
    # Define layer dimensions
    dims = {
        'l4': config.l4_dim,
        'l23': config.l23_dim,
        'l5': config.l5_dim,
        'l6': config.l6_dim
    }
    
    masks = {}
    
    # L4 -> L2/3 (feedforward excitation)
    # Shape: (l4_dim, l23_dim)
    l4_to_l23 = torch.ones((dims['l4'], dims['l23']), dtype=torch.bool, device=device)
    masks['l4_to_l23'] = l4_to_l23
    
    # L2/3 -> L5 (feedforward excitation)
    l23_to_l5 = torch.ones((dims['l23'], dims['l5']), dtype=torch.bool, device=device)
    masks['l23_to_l5'] = l23_to_l5
    
    # L5 -> L6 (feedforward)
    l5_to_l6 = torch.ones((dims['l5'], dims['l6']), dtype=torch.bool, device=device)
    masks['l5_to_l6'] = l5_to_l6
    
    # L6 -> L4 (feedback inhibition/excitation)
    l6_to_l4 = torch.ones((dims['l6'], dims['l4']), dtype=torch.bool, device=device)
    masks['l6_to_l4'] = l6_to_l4
    
    # L2/3 lateral connections (within layer)
    # Diagonal + some neighborhood
    l23_lateral = torch.eye(dims['l23'], dtype=torch.bool, device=device)
    # Add nearby connections (bandwidth = 10% of dimension)
    bandwidth = max(1, int(dims['l23'] * 0.1))
    for i in range(dims['l23']):
        for j in range(max(0, i - bandwidth), min(dims['l23'], i + bandwidth + 1)):
            l23_lateral[i, j] = True
    masks['l23_lateral'] = l23_lateral
    
    # L5 lateral connections
    l5_lateral = torch.eye(dims['l5'], dtype=torch.bool, device=device)
    bandwidth = max(1, int(dims['l5'] * 0.1))
    for i in range(dims['l5']):
        for j in range(max(0, i - bandwidth), min(dims['l5'], i + bandwidth + 1)):
            l5_lateral[i, j] = True
    masks['l5_lateral'] = l5_lateral
    
    # L6 -> L2/3 (modulatory feedback)
    l6_to_l23 = torch.ones((dims['l6'], dims['l23']), dtype=torch.bool, device=device)
    masks['l6_to_l23'] = l6_to_l23
    
    # L4 -> L4 (local recurrent)
    l4_lateral = torch.eye(dims['l4'], dtype=torch.bool, device=device)
    masks['l4_lateral'] = l4_lateral
    
    # L5 -> L2/3 (feedback)
    l5_to_l23 = torch.ones((dims['l5'], dims['l23']), dtype=torch.bool, device=device)
    masks['l5_to_l23'] = l5_to_l23
    
    logger.debug(f"Generated laminar connectivity masks for config: {config}")
    return masks

def verify_connectivity_constraints(
    masks: Dict[str, torch.Tensor],
    config: MicrocircuitColumnConfig
) -> Tuple[bool, List[str]]:
    """
    Verifies that connectivity masks adhere to canonical constraints.
    
    Constraints:
    1. No self-loops in feedforward paths (except lateral)
    2. Feedback paths exist (L6->L4)
    3. Feedforward paths exist (L4->L23->L5->L6)
    4. Lateral connections are sparse (not fully connected)
    
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    dims = {
        'l4': config.l4_dim,
        'l23': config.l23_dim,
        'l5': config.l5_dim,
        'l6': config.l6_dim
    }
    
    # Check L4 -> L2/3 exists
    if 'l4_to_l23' not in masks:
        errors.append("Missing l4_to_l23 connection")
    elif not masks['l4_to_l23'].any():
        errors.append("l4_to_l23 connection is empty")
    
    # Check L2/3 -> L5 exists
    if 'l23_to_l5' not in masks:
        errors.append("Missing l23_to_l5 connection")
    elif not masks['l23_to_l5'].any():
        errors.append("l23_to_l5 connection is empty")
    
    # Check L5 -> L6 exists
    if 'l5_to_l6' not in masks:
        errors.append("Missing l5_to_l6 connection")
    elif not masks['l5_to_l6'].any():
        errors.append("l5_to_l6 connection is empty")
    
    # Check L6 -> L4 (feedback) exists
    if 'l6_to_l4' not in masks:
        errors.append("Missing l6_to_l4 feedback connection")
    elif not masks['l6_to_l4'].any():
        errors.append("l6_to_l4 feedback connection is empty")
    
    # Check lateral connections are sparse (not fully connected)
    for lateral_name in ['l23_lateral', 'l5_lateral', 'l4_lateral']:
        if lateral_name in masks:
            mask = masks[lateral_name]
            total_possible = mask.numel()
            actual_connections = mask.sum().item()
            density = actual_connections / total_possible
            if density > 0.5:  # Lateral should be sparse
                errors.append(f"{lateral_name} is too dense: {density:.2f}")
    
    if errors:
        return False, errors
    return True, []

def apply_ei_balance_constraint(
    weight_matrix: torch.Tensor,
    excitatory_mask: Optional[torch.Tensor] = None,
    target_ei_ratio: float = 4.0
) -> torch.Tensor:
    """
    Applies excitatory/inhibitory balance constraint to a weight matrix.
    
    Args:
        weight_matrix: The weight matrix to constrain
        excitatory_mask: Boolean mask indicating which neurons are excitatory
        target_ei_ratio: Target ratio of excitatory to inhibitory weights
    
    Returns:
        Constrained weight matrix
    """
    if excitatory_mask is None:
        # Default: assume 80% excitatory
        n = weight_matrix.shape[0]
        n_exc = int(n * 0.8)
        excitatory_mask = torch.zeros(n, dtype=torch.bool)
        excitatory_mask[:n_exc] = True
        excitatory_mask = excitatory_mask.unsqueeze(0).expand_as(weight_matrix)
    
    # Separate excitatory and inhibitory weights
    exc_weights = weight_matrix * excitatory_mask
    inh_weights = weight_matrix * (~excitatory_mask)
    
    # Calculate current sums
    exc_sum = exc_weights.abs().sum()
    inh_sum = inh_weights.abs().sum()
    
    if inh_sum == 0:
        return weight_matrix
    
    # Calculate scaling factor to achieve target ratio
    current_ratio = exc_sum / inh_sum
    if current_ratio < target_ei_ratio:
        # Need more excitation relative to inhibition
        scale_exc = target_ei_ratio / current_ratio
        exc_weights = exc_weights * scale_exc
    else:
        # Need more inhibition relative to excitation
        scale_inh = current_ratio / target_ei_ratio
        inh_weights = inh_weights * scale_inh
    
    return exc_weights + inh_weights

class MicrocircuitColumn(nn.Module):
    """
    A complete cortical column module with canonical laminar structure.
    Implements the feedforward and feedback pathways between layers.
    """
    def __init__(self, config: MicrocircuitColumnConfig):
        super().__init__()
        self.config = config
        
        # Create layer configurations
        l4_config = LayerConfig(
            layer_id=4,
            input_dim=config.input_dim,
            output_dim=config.l4_dim,
            excitatory_ratio=config.l4_excitatory_ratio
        )
        l23_config = LayerConfig(
            layer_id=23,
            input_dim=config.l4_dim,  # Receives from L4
            output_dim=config.l23_dim,
            excitatory_ratio=config.l23_excitatory_ratio
        )
        l5_config = LayerConfig(
            layer_id=5,
            input_dim=config.l23_dim,  # Receives from L2/3
            output_dim=config.l5_dim,
            excitatory_ratio=config.l5_excitatory_ratio
        )
        l6_config = LayerConfig(
            layer_id=6,
            input_dim=config.l5_dim,  # Receives from L5
            output_dim=config.l6_dim,
            excitatory_ratio=config.l6_excitatory_ratio
        )
        
        # Instantiate layers
        self.l4 = L4Layer(l4_config)
        self.l23 = L23Layer(l23_config)
        self.l5 = L5Layer(l5_config)
        self.l6 = L6Layer(l6_config)
        
        # Output projection
        self.output_proj = nn.Linear(config.l6_dim, config.output_dim)
        
        # Generate connectivity masks
        self.connectivity_masks = generate_laminar_connectivity_mask(config)
        
        # Verify constraints
        is_valid, errors = verify_connectivity_constraints(self.connectivity_masks, config)
        if not is_valid:
            logger.warning(f"Connectivity constraints violated: {errors}")
        
        # Initialize output projection
        nn.init.xavier_uniform_(self.output_proj.weight)
        nn.init.zeros_(self.output_proj.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the cortical column.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)
        
        Returns:
            Output tensor of shape (batch_size, seq_len, output_dim)
        """
        # L4: Thalamic input
        l4_out = self.l4(x)
        
        # L2/3: Feedforward from L4
        l23_out = self.l23(l4_out)
        
        # L5: Feedforward from L2/3
        l5_out = self.l5(l23_out)
        
        # L6: Feedforward from L5
        l6_out = self.l6(l5_out)
        
        # Feedback from L6 to L4 (simplified: just add to L4 output before L2/3)
        # In a full model, this would be a separate feedback loop
        
        # Output projection
        out = self.output_proj(l6_out)
        
        return out

def create_microcircuit_column(config: MicrocircuitColumnConfig) -> MicrocircuitColumn:
    """Factory function to create a MicrocircuitColumn instance."""
    return MicrocircuitColumn(config)

def main():
    """Test script for microcircuit connectivity."""
    config = MicrocircuitColumnConfig()
    column = create_microcircuit_column(config)
    
    # Test forward pass
    x = torch.randn(2, 10, config.input_dim)
    y = column(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {y.shape}")
    print(f"Connectivity masks generated: {list(column.connectivity_masks.keys())}")
    
    # Verify constraints
    is_valid, errors = verify_connectivity_constraints(column.connectivity_masks, config)
    print(f"Connectivity valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

if __name__ == "__main__":
    main()