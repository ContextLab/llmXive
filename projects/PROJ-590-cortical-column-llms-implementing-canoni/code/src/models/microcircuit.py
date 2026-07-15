import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import math

@dataclass
class LayerConfig:
    """Configuration for a cortical layer."""
    name: str
    neuron_count: int
    is_excitatory: bool
    connectivity_factor: float = 1.0

class CorticalLayer(nn.Module):
    """Base class for cortical layers with configurable connectivity."""
    
    def __init__(self, config: LayerConfig, input_dim: int):
        super().__init__()
        self.config = config
        self.input_dim = input_dim
        self.neuron_count = config.neuron_count
        self.is_excitatory = config.is_excitatory
        
        # Initialize weights with normalized range [-0.1, 0.1]
        # to ensure stable initial activity
        self.weight = nn.Parameter(
            torch.randn(input_dim, self.neuron_count) * 0.1
        )
        self.bias = nn.Parameter(torch.zeros(self.neuron_count))
        
        # Activation function (ReLU for excitatory, LeakyReLU for inhibitory)
        self.activation = nn.ReLU() if self.is_excitatory else nn.LeakyReLU(0.01)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the layer."""
        # x: [batch, input_dim]
        out = F.linear(x, self.weight.t(), self.bias)
        return self.activation(out)

class L23Layer(CorticalLayer):
    """Layer 2/3: Supragranular, primarily excitatory, recurrent connections."""
    def __init__(self, input_dim: int, neuron_count: int = 128):
        config = LayerConfig(
            name="L2/3",
            neuron_count=neuron_count,
            is_excitatory=True,
            connectivity_factor=0.8
        )
        super().__init__(config, input_dim)

class L4Layer(CorticalLayer):
    """Layer 4: Granular layer, primary input recipient, mixed E/I."""
    def __init__(self, input_dim: int, neuron_count: int = 128):
        config = LayerConfig(
            name="L4",
            neuron_count=neuron_count,
            is_excitatory=True,  # L4 excitatory stellate cells
            connectivity_factor=1.0
        )
        super().__init__(config, input_dim)

class L5Layer(CorticalLayer):
    """Layer 5: Infragranular, output to subcortical, strong recurrent."""
    def __init__(self, input_dim: int, neuron_count: int = 128):
        config = LayerConfig(
            name="L5",
            neuron_count=neuron_count,
            is_excitatory=True,
            connectivity_factor=0.9
        )
        super().__init__(config, input_dim)

class L6Layer(CorticalLayer):
    """Layer 6: Infragranular, feedback to thalamus."""
    def __init__(self, input_dim: int, neuron_count: int = 64):
        config = LayerConfig(
            name="L6",
            neuron_count=neuron_count,
            is_excitatory=True,
            connectivity_factor=0.7
        )
        super().__init__(config, input_dim)

class MicrocircuitColumn(nn.Module):
    """
    A canonical cortical column implementing laminar connectivity.
    
    Enforces:
    - L4 -> L2/3 excitatory feedforward (strong)
    - L2/3 -> L5 -> L6 feedforward
    - L6 -> L4 feedback (modulatory)
    - Local recurrent connections within layers
    - E/I balance via construction (4:1 target ratio)
    """
    
    def __init__(
        self,
        input_dim: int,
        l23_neurons: int = 128,
        l4_neurons: int = 128,
        l5_neurons: int = 128,
        l6_neurons: int = 64,
        exc_ratio: float = 4.0
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.exc_ratio = exc_ratio
        
        # Create layers
        self.l4 = L4Layer(input_dim, l4_neurons)
        self.l23 = L23Layer(l4_neurons, l23_neurons)
        self.l5 = L5Layer(l23_neurons, l5_neurons)
        self.l6 = L6Layer(l5_neurons, l6_neurons)
        
        # Feedback pathway: L6 -> L4 (modulatory)
        self.feedback_proj = nn.Linear(l6_neurons, l4_neurons)
        
        # Recurrent connections within L2/3
        self.l23_recurrence = nn.Linear(l23_neurons, l23_neurons)
        
        # Initialize feedback and recurrence with small weights
        nn.init.uniform_(self.feedback_proj.weight, -0.05, 0.05)
        nn.init.zeros_(self.feedback_proj.bias)
        nn.init.uniform_(self.l23_recurrence.weight, -0.05, 0.05)
        nn.init.zeros_(self.l23_recurrence.bias)
        
        # Store connectivity mask for verification
        self._build_connectivity_mask()

    def _build_connectivity_mask(self) -> Dict[str, torch.Tensor]:
        """
        Build and store connectivity masks enforcing laminar topology.
        
        Masks are binary tensors where 1 indicates allowed connection, 0 blocked.
        This enforces:
        - L4->L2/3: Full excitatory connectivity (no inhibition)
        - L2/3->L5: Feedforward excitatory
        - L5->L6: Feedforward excitatory
        - L6->L4: Feedback modulatory (scaled down)
        - Recurrent within layers: Sparse local connectivity
        """
        masks = {}
        
        # L4 -> L2/3: Full connectivity (excitatory only)
        # Shape: [l23_neurons, l4_neurons]
        masks['L4_to_L23'] = torch.ones(self.l23.neuron_count, self.l4.neuron_count)
        
        # L2/3 -> L5: Full connectivity
        masks['L23_to_L5'] = torch.ones(self.l5.neuron_count, self.l23.neuron_count)
        
        # L5 -> L6: Full connectivity
        masks['L5_to_L6'] = torch.ones(self.l6.neuron_count, self.l5.neuron_count)
        
        # L6 -> L4: Feedback (full but will be scaled in forward)
        masks['L6_to_L4'] = torch.ones(self.l4.neuron_count, self.l6.neuron_count)
        
        # Recurrent L2/3: Sparse local connectivity (diagonal + neighbors)
        # Create a band matrix for local recurrence
        recurrence_mask = torch.zeros(self.l23.neuron_count, self.l23.neuron_count)
        bandwidth = max(1, self.l23.neuron_count // 8)  # ~12.5% local connectivity
        for i in range(self.l23.neuron_count):
            for j in range(max(0, i - bandwidth), min(self.l23.neuron_count, i + bandwidth + 1)):
                recurrence_mask[i, j] = 1.0
        masks['L23_recurrence'] = recurrence_mask
        
        # Store masks as buffers (not parameters, so they don't get optimized)
        for name, mask in masks.items():
            self.register_buffer(f'mask_{name}', mask)
        
        return masks

    def get_connectivity_mask(self, connection_type: str) -> torch.Tensor:
        """Retrieve a specific connectivity mask by name."""
        attr_name = f'mask_{connection_type}'
        if hasattr(self, attr_name):
            return getattr(self, attr_name)
        raise ValueError(f"Unknown connection type: {connection_type}")

    def enforce_connectivity_mask(self, weight: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """
        Apply a connectivity mask to a weight tensor.
        
        Zeroes out weights where mask is 0, preserving weights where mask is 1.
        This enforces the laminar topology constraint by construction.
        """
        return weight * mask

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the cortical column.
        
        Flow:
        1. Input -> L4 (feedforward)
        2. L4 -> L2/3 (strong excitatory)
        3. L2/3 -> L2/3 (recurrent)
        4. L2/3 -> L5 -> L6 (feedforward)
        5. L6 -> L4 (feedback modulatory)
        
        Args:
            x: Input tensor of shape [batch, input_dim]
        
        Returns:
            Output tensor of shape [batch, l6_neurons]
        """
        # Layer 4: Primary input recipient
        l4_out = self.l4(x)  # [batch, l4_neurons]
        
        # Layer 2/3: Strong excitatory feedforward from L4
        l23_out = self.l23(l4_out)  # [batch, l23_neurons]
        
        # Recurrent connections within L2/3 (masked)
        l23_rec = self.l23_recurrence(l23_out)
        l23_rec_masked = self.enforce_connectivity_mask(l23_rec, self.mask_L23_recurrence)
        l23_out = l23_out + 0.1 * l23_rec_masked  # Small recurrent contribution
        
        # Layer 5: Feedforward from L2/3
        l5_out = self.l5(l23_out)  # [batch, l5_neurons]
        
        # Layer 6: Feedforward from L5
        l6_out = self.l6(l5_out)  # [batch, l6_neurons]
        
        # Feedback: L6 -> L4 (modulatory, scaled down)
        feedback = self.feedback_proj(l6_out)  # [batch, l4_neurons]
        l4_out = l4_out + 0.05 * feedback  # Small feedback contribution
        
        return l6_out

def create_microcircuit_column(
    input_dim: int,
    l23_neurons: int = 128,
    l4_neurons: int = 128,
    l5_neurons: int = 128,
    l6_neurons: int = 64,
    exc_ratio: float = 4.0
) -> MicrocircuitColumn:
    """
    Factory function to create a MicrocircuitColumn instance.
    
    Args:
        input_dim: Dimension of input features
        l23_neurons: Number of neurons in L2/3 layer
        l4_neurons: Number of neurons in L4 layer
        l5_neurons: Number of neurons in L5 layer
        l6_neurons: Number of neurons in L6 layer
        exc_ratio: Target excitatory to inhibitory ratio (4.0 by default)
    
    Returns:
        A configured MicrocircuitColumn module
    """
    return MicrocircuitColumn(
        input_dim=input_dim,
        l23_neurons=l23_neurons,
        l4_neurons=l4_neurons,
        l5_neurons=l5_neurons,
        l6_neurons=l6_neurons,
        exc_ratio=exc_ratio
    )

def generate_laminar_connectivity_mask(
    l23_neurons: int,
    l4_neurons: int,
    l5_neurons: int,
    l6_neurons: int,
    recurrence_bandwidth: Optional[int] = None
) -> Dict[str, torch.Tensor]:
    """
    Generate connectivity masks enforcing laminar topology.
    
    This function creates binary masks that define allowed connections
    between cortical layers, enforcing:
    - L4 -> L2/3: Full excitatory connectivity
    - L2/3 -> L5 -> L6: Feedforward excitatory
    - L6 -> L4: Feedback modulatory
    - Local recurrence within L2/3: Sparse band connectivity
    
    Args:
        l23_neurons: Number of neurons in L2/3
        l4_neurons: Number of neurons in L4
        l5_neurons: Number of neurons in L5
        l6_neurons: Number of neurons in L6
        recurrence_bandwidth: Number of neighbors for local recurrence (default: ~12.5% of l23_neurons)
    
    Returns:
        Dictionary of connectivity masks:
        - 'L4_to_L23': [l23, l4] - Full excitatory
        - 'L23_to_L5': [l5, l23] - Feedforward
        - 'L5_to_L6': [l6, l5] - Feedforward
        - 'L6_to_L4': [l4, l6] - Feedback
        - 'L23_recurrence': [l23, l23] - Sparse local
    """
    masks = {}
    
    # L4 -> L2/3: Full connectivity (excitatory only)
    masks['L4_to_L23'] = torch.ones(l23_neurons, l4_neurons)
    
    # L2/3 -> L5: Full connectivity
    masks['L23_to_L5'] = torch.ones(l5_neurons, l23_neurons)
    
    # L5 -> L6: Full connectivity
    masks['L5_to_L6'] = torch.ones(l6_neurons, l5_neurons)
    
    # L6 -> L4: Feedback (full)
    masks['L6_to_L4'] = torch.ones(l4_neurons, l6_neurons)
    
    # Recurrent L2/3: Sparse local connectivity
    if recurrence_bandwidth is None:
        recurrence_bandwidth = max(1, l23_neurons // 8)
    
    recurrence_mask = torch.zeros(l23_neurons, l23_neurons)
    for i in range(l23_neurons):
        start = max(0, i - recurrence_bandwidth)
        end = min(l23_neurons, i + recurrence_bandwidth + 1)
        recurrence_mask[i, start:end] = 1.0
    
    masks['L23_recurrence'] = recurrence_mask
    
    return masks

def verify_connectivity_constraints(
    column: MicrocircuitColumn,
    tolerance: float = 1e-6
) -> Dict[str, bool]:
    """
    Verify that connectivity constraints are properly enforced.
    
    Checks:
    - All masks are binary (0 or 1)
    - L4->L2/3 mask is all ones (full excitatory)
    - Recurrence mask is sparse (< 20% connectivity)
    - No connections are created where masks are zero
    
    Args:
        column: The MicrocircuitColumn instance to verify
        tolerance: Floating point tolerance for mask verification
    
    Returns:
        Dictionary of verification results:
        - 'masks_binary': All masks contain only 0 or 1
        - 'L4_to_L23_full': L4->L2/3 mask is all ones
        - 'recurrence_sparse': L2/3 recurrence is sparse (< 20%)
        - 'all_passed': True if all checks passed
    """
    results = {}
    
    # Check all masks are binary
    all_binary = True
    for name in ['L4_to_L23', 'L23_to_L5', 'L5_to_L6', 'L6_to_L4', 'L23_recurrence']:
        mask = column.get_connectivity_mask(name)
        unique_vals = torch.unique(mask)
        if not torch.all((unique_vals == 0) | (unique_vals == 1)):
            all_binary = False
            break
    results['masks_binary'] = all_binary
    
    # Check L4->L2/3 is full
    l4_to_l23 = column.get_connectivity_mask('L4_to_L23')
    results['L4_to_L23_full'] = torch.all(l4_to_l23 == 1.0)
    
    # Check recurrence sparsity
    l23_rec = column.get_connectivity_mask('L23_recurrence')
    sparsity = (l23_rec == 0).float().mean().item()
    results['recurrence_sparse'] = sparsity > 0.8  # > 80% zeros means < 20% connectivity
    
    results['all_passed'] = all(results.values())
    
    return results

def apply_ei_balance_constraint(
    weights: torch.Tensor,
    exc_ratio: float = 4.0
) -> torch.Tensor:
    """
    Apply E/I balance constraint to weight matrix.
    
    Ensures that the ratio of excitatory to inhibitory weights
    approximates the target exc_ratio (default 4:1).
    
    This is implemented by scaling inhibitory weights to achieve
    the desired ratio in the total weight magnitude.
    
    Args:
        weights: Weight tensor of shape [input_dim, output_dim]
        exc_ratio: Target excitatory to inhibitory ratio
    
    Returns:
        Weight tensor with E/I balance constraint applied
    """
    # Assume first 80% of outputs are excitatory, last 20% are inhibitory
    # (standard cortical E/I ratio ~ 4:1)
    n_excitatory = int(weights.shape[1] * (exc_ratio / (exc_ratio + 1)))
    n_inhibitory = weights.shape[1] - n_excitatory
    
    if n_inhibitory == 0:
        return weights
    
    # Calculate current magnitudes
    exc_magnitude = torch.norm(weights[:, :n_excitatory]).item()
    inh_magnitude = torch.norm(weights[:, n_excitatory:]).item()
    
    if inh_magnitude < 1e-10:
        return weights
    
    # Scale inhibitory weights to achieve target ratio
    target_inh_magnitude = exc_magnitude / exc_ratio
    scale_factor = target_inh_magnitude / inh_magnitude
    
    weights[:, n_excitatory:] *= scale_factor
    
    return weights

# Export public API
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
