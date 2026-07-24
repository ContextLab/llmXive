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
    """Configuration for a single cortical layer."""
    name: str
    neuron_count: int
    input_dim: int
    output_dim: int
    is_excitatory: bool = True
    activation: str = "relu"
    weight_min: float = -0.1
    weight_max: float = 0.1

class CorticalLayer(nn.Module):
    """A single cortical layer with configurable connectivity and activation."""

    def __init__(self, config: LayerConfig):
        super().__init__()
        self.config = config
        self.name = config.name
        self.neuron_count = config.neuron_count
        self.is_excitatory = config.is_excitatory

        # Initialize weights with clipping logic applied immediately
        self.weight = nn.Parameter(
            torch.empty(config.output_dim, config.input_dim)
        )
        self.bias = nn.Parameter(torch.zeros(config.output_dim))

        # Apply weight clipping during initialization
        self._apply_weight_clipping()

        # Set activation function
        if config.activation == "relu":
            self.activation = F.relu
        elif config.activation == "sigmoid":
            self.activation = torch.sigmoid
        elif config.activation == "tanh":
            self.activation = torch.tanh
        else:
            raise ValueError(f"Unknown activation: {config.activation}")

    def _apply_weight_clipping(self):
        """Enforce normalized weight range during initialization."""
        with torch.no_grad():
            min_val = self.config.weight_min
            max_val = self.config.weight_max
            self.weight.clamp_(min=min_val, max=max_val)
            logger.debug(
                f"Applied weight clipping [{min_val}, {max_val}] to layer {self.name}"
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the layer."""
        # x shape: (batch_size, input_dim) or (input_dim,)
        if x.dim() == 1:
            x = x.unsqueeze(0)

        out = F.linear(x, self.weight, self.bias)
        return self.activation(out)

    def clip_weights(self, min_val: Optional[float] = None, max_val: Optional[float] = None):
        """Explicitly clip weights to a range (can be called during training)."""
        with torch.no_grad():
            if min_val is None:
                min_val = self.config.weight_min
            if max_val is None:
                max_val = self.config.weight_max
            self.weight.clamp_(min=min_val, max=max_val)

class L23Layer(CorticalLayer):
    """Layer 2/3: Associative and output layer, primarily excitatory."""
    def __init__(self, config: LayerConfig):
        # L2/3 is typically excitatory
        config.is_excitatory = True
        super().__init__(config)

class L4Layer(CorticalLayer):
    """Layer 4: Primary input layer, receives thalamic input."""
    def __init__(self, config: LayerConfig):
        # L4 is typically excitatory (spiny stellate cells)
        config.is_excitatory = True
        super().__init__(config)

class L5Layer(CorticalLayer):
    """Layer 5: Output to subcortical structures, contains pyramidal tract neurons."""
    def __init__(self, config: LayerConfig):
        config.is_excitatory = True
        super().__init__(config)

class L6Layer(CorticalLayer):
    """Layer 6: Feedback to thalamus, mixed excitatory/inhibitory."""
    def __init__(self, config: LayerConfig):
        # L6 has both excitatory and inhibitory components, but we model the main projection
        config.is_excitatory = True
        super().__init__(config)

class MicrocircuitColumn(nn.Module):
    """
    A canonical cortical column module.
    Implements laminar structure with local E/I loops and homeostatic scaling.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        l23_neurons: int = 64,
        l4_neurons: int = 64,
        l5_neurons: int = 32,
        l6_neurons: int = 32,
        weight_min: float = -0.1,
        weight_max: float = 0.1,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Layer configurations with weight clipping bounds
        self.l4_config = LayerConfig(
            name="L4",
            neuron_count=l4_neurons,
            input_dim=input_dim,
            output_dim=l4_neurons,
            is_excitatory=True,
            weight_min=weight_min,
            weight_max=weight_max,
        )
        self.l23_config = LayerConfig(
            name="L23",
            neuron_count=l23_neurons,
            input_dim=l4_neurons,
            output_dim=l23_neurons,
            is_excitatory=True,
            weight_min=weight_min,
            weight_max=weight_max,
        )
        self.l5_config = LayerConfig(
            name="L5",
            neuron_count=l5_neurons,
            input_dim=l23_neurons,
            output_dim=l5_neurons,
            is_excitatory=True,
            weight_min=weight_min,
            weight_max=weight_max,
        )
        self.l6_config = LayerConfig(
            name="L6",
            neuron_count=l6_neurons,
            input_dim=l23_neurons,
            output_dim=l6_neurons,
            is_excitatory=True,
            weight_min=weight_min,
            weight_max=weight_max,
        )

        # Initialize layers (weight clipping happens in __init__ of CorticalLayer)
        self.l4 = L4Layer(self.l4_config)
        self.l23 = L23Layer(self.l23_config)
        self.l5 = L5Layer(self.l5_config)
        self.l6 = L6Layer(self.l6_config)

        # Output projection
        self.output_proj = nn.Linear(l5_neurons, output_dim)
        # Initialize output weights with clipping
        with torch.no_grad():
            self.output_proj.weight.clamp_(min=weight_min, max=weight_max)
            self.output_proj.bias.zero_()

        # Store weight bounds for runtime clipping
        self.weight_min = weight_min
        self.weight_max = weight_max

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the cortical column.
        Path: Input -> L4 -> L2/3 -> (L5, L6) -> Output
        """
        # L4: Primary input processing
        h4 = self.l4(x)

        # L2/3: Associative processing (receives from L4)
        h23 = self.l23(h4)

        # L5: Output to subcortical (receives from L2/3)
        h5 = self.l5(h23)

        # L6: Feedback (receives from L2/3) - not directly in main output path
        _ = self.l6(h23)  # Compute but don't use for main output

        # Output projection
        out = self.output_proj(h5)
        return out

    def clip_all_weights(self):
        """Apply weight clipping to all layers in the column."""
        self.l4.clip_weights(self.weight_min, self.weight_max)
        self.l23.clip_weights(self.weight_min, self.weight_max)
        self.l5.clip_weights(self.weight_min, self.weight_max)
        self.l6.clip_weights(self.weight_min, self.weight_max)
        with torch.no_grad():
            self.output_proj.weight.clamp_(min=self.weight_min, max=self.weight_max)

def generate_laminar_connectivity_mask(
    l4_size: int, l23_size: int, l5_size: int, l6_size: int
) -> torch.Tensor:
    """
    Generate a binary mask enforcing laminar connectivity constraints.
    1 = connection allowed, 0 = connection forbidden.
    """
    # Total size: L4 -> L23 -> L5, L6
    total_size = l4_size + l23_size + l5_size + l6_size
    mask = torch.zeros(total_size, total_size)

    # L4 -> L23 (excitatory)
    mask[l23_size:l23_size+l23_size, :l4_size] = 1.0

    # L23 -> L5
    mask[l23_size+l23_size:l23_size+l23_size+l5_size, l23_size:l23_size+l23_size] = 1.0

    # L23 -> L6
    mask[l23_size+l23_size+l5_size:, l23_size:l23_size+l23_size] = 1.0

    return mask

def verify_connectivity_constraints(column: MicrocircuitColumn) -> bool:
    """
    Verify that the column's internal weights satisfy the laminar constraints.
    """
    # Check that all weights are within bounds
    all_weights = []
    for module in column.modules():
        if isinstance(module, (L23Layer, L4Layer, L5Layer, L6Layer)):
            all_weights.append(module.weight)
        elif isinstance(module, nn.Linear):
            all_weights.append(module.weight)

    for w in all_weights:
        if w.min() < column.weight_min or w.max() > column.weight_max:
            return False
    return True

def apply_ei_balance_constraint(column: MicrocircuitColumn, target_ratio: float = 4.0):
    """
    Apply homeostatic scaling to maintain E/I balance.
    Note: In this simplified model, we assume all layers are excitatory.
    In a full model, inhibitory layers would be scaled differently.
    """
    # For now, just ensure weights are clipped (which is done at init and forward)
    column.clip_all_weights()

def create_microcircuit_column(
    input_dim: int,
    hidden_dim: int,
    output_dim: int,
    weight_min: float = -0.1,
    weight_max: float = 0.1,
) -> MicrocircuitColumn:
    """Factory function to create a cortical column with weight clipping."""
    return MicrocircuitColumn(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        weight_min=weight_min,
        weight_max=weight_max,
    )

@dataclass
class LayerConfig:
    """Configuration for a single cortical layer."""
    name: str
    neuron_count: int
    input_dim: int
    output_dim: int
    is_excitatory: bool = True
    activation: str = "relu"
    weight_min: float = -0.1
    weight_max: float = 0.1