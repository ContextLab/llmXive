"""
Prefrontal Gating Module for Neural Narrative Networks.

This module implements a prefrontal cortex-inspired gating mechanism that
distinguishes between 'plot' (coherence/semantic flow) and 'memory'
(episodic trace/long-term dependencies) signals during narrative generation.

Inspired by Dan Rockmore's feedback on distinguishing plot structure from
memory traces, and Eric Kandel's distinction between transient and
consolidated modifications.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any

from config import get_config
from utils.logging_config import get_logger, info, error, warning

logger = get_logger(__name__)


class PrefrontalGatingModule(nn.Module):
    """
    A gating module that separates plot (coherence) and memory (episodic) pathways.

    Architecture:
    - Input: Hidden states from the narrative encoder (e.g., SAE or LSTM)
    - Plot Pathway: Focuses on local coherence, syntax, and immediate context.
    - Memory Pathway: Focuses on long-term dependencies, episodic traces, and consistency.
    - Gating Mechanism: Learnable sigmoid gates that modulate the contribution
      of each pathway to the final representation.

    This design reflects the prefrontal cortex's role in executive control,
    balancing immediate goals (plot) with long-term context (memory).
    """

    def __init__(
        self,
        hidden_dim: int,
        plot_dim: int = 128,
        memory_dim: int = 128,
        gate_dim: int = 64,
        dropout: float = 0.1
    ):
        super().__init__()

        self.hidden_dim = hidden_dim
        self.plot_dim = plot_dim
        self.memory_dim = memory_dim
        self.gate_dim = gate_dim

        # Plot pathway: focuses on immediate coherence
        # Uses a smaller receptive field implicitly via dense projection
        self.plot_projection = nn.Linear(hidden_dim, plot_dim)
        self.plot_transform = nn.Sequential(
            nn.Linear(plot_dim, plot_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # Memory pathway: focuses on episodic traces
        # Can incorporate attention to past states if needed, but here
        # we project to a dedicated memory space
        self.memory_projection = nn.Linear(hidden_dim, memory_dim)
        self.memory_transform = nn.Sequential(
            nn.Linear(memory_dim, memory_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # Gating mechanism: determines how much of each pathway to use
        # based on the current context
        self.gate_network = nn.Sequential(
            nn.Linear(hidden_dim, gate_dim),
            nn.Tanh(),
            nn.Linear(gate_dim, 2),  # 2 gates: one for plot, one for memory
            nn.Sigmoid()
        )

        # Final fusion layer
        self.fusion = nn.Linear(plot_dim + memory_dim, hidden_dim)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with Xavier uniform for stability."""
        for module in [self.plot_projection, self.memory_projection, self.gate_network[0], self.gate_network[2], self.fusion]:
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        hidden_states: torch.Tensor,
        memory_context: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Dict[str, Any]]:
        """
        Forward pass through the gating module.

        Args:
            hidden_states: Tensor of shape (batch_size, seq_len, hidden_dim)
                representing the current narrative state.
            memory_context: Optional tensor of shape (batch_size, seq_len, memory_dim)
                representing pre-extracted episodic memory traces. If None,
                the memory pathway will derive its trace from hidden_states.

        Returns:
            Tuple containing:
            - gated_output: Final fused representation (batch_size, seq_len, hidden_dim)
            - plot_signal: Activations from the plot pathway
            - memory_signal: Activations from the memory pathway
            - metadata: Dict with gate values and pathway statistics
        """
        batch_size, seq_len, _ = hidden_states.shape

        # 1. Plot Pathway: Extract coherence features
        plot_features = self.plot_projection(hidden_states)
        plot_signal = self.plot_transform(plot_features)

        # 2. Memory Pathway: Extract episodic features
        if memory_context is not None:
            # Use provided memory context if available
            memory_features = self.memory_projection(memory_context)
        else:
            # Derive memory trace from current hidden states (short-term consolidation)
            memory_features = self.memory_projection(hidden_states)

        memory_signal = self.memory_transform(memory_features)

        # 3. Compute Gating Weights
        # The gate decides how much to trust plot vs. memory for each position
        gate_logits = self.gate_network(hidden_states)
        gates = torch.softmax(gate_logits, dim=-1)  # Shape: (batch, seq, 2)

        # Split gates
        plot_gate = gates[:, :, 0:1]  # Shape: (batch, seq, 1)
        memory_gate = gates[:, :, 1:2]  # Shape: (batch, seq, 1)

        # 4. Apply Gating
        gated_plot = plot_signal * plot_gate
        gated_memory = memory_signal * memory_gate

        # 5. Fuse pathways
        combined = torch.cat([gated_plot, gated_memory], dim=-1)
        gated_output = self.fusion(combined)

        # 6. Gather metadata for diagnostics
        metadata = {
            'plot_gate_mean': float(plot_gate.mean().item()),
            'memory_gate_mean': float(memory_gate.mean().item()),
            'plot_signal_norm': float(torch.norm(plot_signal).item()),
            'memory_signal_norm': float(torch.norm(memory_signal).item()),
            'gate_entropy': float(-(gates * torch.log(gates + 1e-8)).sum(dim=-1).mean().item())
        }

        return gated_output, plot_signal, memory_signal, metadata


def create_prefrontal_gating_module(
    input_dim: int,
    config_dict: Optional[Dict[str, Any]] = None
) -> PrefrontalGatingModule:
    """
    Factory function to create a PrefrontalGatingModule with appropriate dimensions.

    Args:
        input_dim: The dimensionality of the input hidden states.
        config_dict: Optional dict with override parameters (plot_dim, memory_dim, etc.)

    Returns:
        A configured PrefrontalGatingModule instance.
    """
    cfg = get_config()
    default_params = {
        'hidden_dim': input_dim,
        'plot_dim': 128,
        'memory_dim': 128,
        'gate_dim': 64,
        'dropout': 0.1
    }

    if config_dict:
        default_params.update(config_dict)

    logger.info(f"Creating PrefrontalGatingModule with hidden_dim={input_dim}")
    return PrefrontalGatingModule(**default_params)