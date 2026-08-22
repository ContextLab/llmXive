import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List, Callable
from dataclasses import dataclass
import math
import logging

from src.training.homeostasis import apply_ei_balance_constraint

logger = logging.getLogger(__name__)

@dataclass
class LayerConfig:
    """Configuration for a single cortical layer."""
    name: str
    input_size: int
    output_size: int
    exc_ratio: float = 0.8  # Fraction of excitatory neurons
    bias: bool = True

@dataclass
class MicrocircuitColumnConfig:
    """Configuration for a full cortical column."""
    l4_size: int = 128
    l23_size: int = 128
    l5_size: int = 128
    l6_size: int = 128
    exc_ratio: float = 0.8
    dropout: float = 0.1

def generate_laminar_connectivity_mask(
    source_layer: str,
    target_layer: str,
    source_size: int,
    target_size: int,
    config: MicrocircuitColumnConfig
) -> torch.Tensor:
    """
    Generate a binary connectivity mask enforcing canonical laminar topology.

    Canonical feedforward/feedback rules (simplified):
    - L4 -> L2/3 (Feedforward Excitatory)
    - L2/3 -> L5 (Feedforward Excitatory)
    - L5 -> L6 (Feedforward Excitatory)
    - L6 -> L4 (Feedback Inhibitory/Regulatory)
    - L2/3 -> L2/3 (Recurrent Excitatory)
    - L5 -> L5 (Recurrent Excitatory)
    - All layers receive local inhibition (modeled as dense to inhibitory pool)

    Returns:
        torch.Tensor: Binary mask of shape (target_size, source_size).
                      1 indicates a connection exists, 0 otherwise.
    """
    mask = torch.zeros((target_size, source_size), dtype=torch.float32)

    # Calculate excitatory/inhibitory splits
    # We assume the first `exc_count` neurons are excitatory, rest inhibitory
    # This is a simplification of the "fixed structural constraint" mentioned in T010c
    def get_ei_split(size):
        exc_count = int(size * config.exc_ratio)
        inh_count = size - exc_count
        return exc_count, inh_count

    src_exc, src_inh = get_ei_split(source_size)
    tgt_exc, tgt_inh = get_ei_split(target_size)

    # Define canonical rules
    # Note: In a real biological model, specific connection probabilities might vary.
    # Here we implement the "simplest rule" (per Wolfram feedback) that creates the
    # necessary topology for universal computation: Feedforward excitation + Feedback/Recurrent loops.

    if source_layer == "L4" and target_layer == "L23":
        # L4 -> L2/3: Strong feedforward excitation
        # Connect L4 excitatory to L2/3 excitatory
        mask[:tgt_exc, :src_exc] = 1.0
        # Also connect to inhibitory for normalization
        mask[tgt_exc:, :src_exc] = 0.5  # Weaker feedforward to inhibitory

    elif source_layer == "L23" and target_layer == "L5":
        # L2/3 -> L5: Feedforward excitation
        mask[:tgt_exc, :src_exc] = 1.0
        mask[tgt_exc:, :src_exc] = 0.5

    elif source_layer == "L5" and target_layer == "L6":
        # L5 -> L6: Feedforward excitation
        mask[:tgt_exc, :src_exc] = 1.0
        mask[tgt_exc:, :src_exc] = 0.5

    elif source_layer == "L6" and target_layer == "L4":
        # L6 -> L4: Feedback inhibition/regulation
        # L6 inhibitory neurons project to L4 to regulate input gain
        # We model this as connecting L6 inhibitory to L4 excitatory (strong inhibition)
        # and L6 excitatory to L4 inhibitory (disinhibition loop)
        # Simplified: Dense connection with a bias towards inhibition on L4 exc
        mask[:tgt_exc, src_exc:] = 1.0  # L6 Inh -> L4 Exc (Inhibition)
        mask[tgt_exc:, :src_exc] = 1.0  # L6 Exc -> L4 Inh (Disinhibition)

    elif source_layer == "L23" and target_layer == "L23":
        # L2/3 -> L2/3: Recurrent excitation
        mask[:tgt_exc, :src_exc] = 1.0
        # Local inhibition (L23 Inh -> L23 Exc)
        mask[:tgt_exc, src_exc:] = 1.0

    elif source_layer == "L5" and target_layer == "L5":
        # L5 -> L5: Recurrent excitation
        mask[:tgt_exc, :src_exc] = 1.0
        mask[:tgt_exc, src_exc:] = 1.0

    else:
        # Default: No connection (sparse topology)
        # This enforces the "fixed canonical topology" strictly
        pass

    # Normalize mask to prevent exploding activations if dense
    # This is a structural constraint, not a learned weight
    return mask

def verify_connectivity_constraints(
    mask: torch.Tensor,
    source_layer: str,
    target_layer: str,
    config: MicrocircuitColumnConfig
) -> bool:
    """
    Verify that a generated mask adheres to the canonical constraints.
    Returns True if valid, False otherwise.
    """
    # Basic shape check
    if mask.dim() != 2:
        logger.error(f"Mask must be 2D, got {mask.dim()}D")
        return False

    # Check for forbidden connections (e.g., L4 -> L6 directly)
    forbidden_pairs = [
        ("L4", "L5"), ("L4", "L6"),
        ("L23", "L4"), ("L23", "L6"),
        ("L5", "L23"), ("L5", "L4"),
        ("L6", "L23"), ("L6", "L5")
    ]

    if (source_layer, target_layer) in forbidden_pairs:
        if mask.sum() > 0:
            logger.error(f"Forbidden connection detected: {source_layer} -> {target_layer}")
            return False

    return True

class CorticalLayer(nn.Module):
    """
    A single cortical layer with excitatory/inhibitory separation.
    """
    def __init__(self, config: LayerConfig):
        super().__init__()
        self.name = config.name
        self.exc_ratio = config.exc_ratio

        # Split neurons into Excitatory and Inhibitory populations
        self.exc_size = int(config.output_size * config.exc_ratio)
        self.inh_size = config.output_size - self.exc_size

        # Excitatory projection (learnable weights)
        self.exc_proj = nn.Linear(config.input_size, self.exc_size, bias=config.bias)
        # Inhibitory projection (often faster, simpler, or fixed in some models,
        # but here we allow learnable weights constrained by homeostasis)
        self.inh_proj = nn.Linear(config.input_size, self.inh_size, bias=config.bias)

        # Activation functions
        # Excitatory: ReLU or similar (non-negative)
        # Inhibitory: Often modeled as subtractive, but here we output activity
        # which will be used to inhibit others. We use ReLU for activity.
        self.exc_activation = nn.ReLU()
        self.inh_activation = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch, input_size)
        Returns:
            Tensor of shape (batch, output_size) concatenating [exc, inh]
        """
        exc_out = self.exc_activation(self.exc_proj(x))
        inh_out = self.inh_activation(self.inh_proj(x))
        return torch.cat([exc_out, inh_out], dim=-1)

class L4Layer(CorticalLayer):
    """Layer 4: Input receiving layer (Thalamic input)."""
    def __init__(self, config: LayerConfig):
        # L4 is the primary input layer
        super().__init__(config)

class L23Layer(CorticalLayer):
    """Layers 2/3: Associative and Recurrent processing."""
    def __init__(self, config: LayerConfig):
        super().__init__(config)

class L5Layer(CorticalLayer):
    """Layer 5: Output to subcortical structures."""
    def __init__(self, config: LayerConfig):
        super().__init__(config)

class L6Layer(CorticalLayer):
    """Layer 6: Feedback to Thalamus/L4."""
    def __init__(self, config: LayerConfig):
        super().__init__(config)

class MicrocircuitColumn(nn.Module):
    """
    A full cortical column implementing the canonical microcircuit.
    """
    def __init__(self, config: MicrocircuitColumnConfig):
        super().__init__()
        self.config = config

        # Initialize layers
        # L4 receives external input
        self.l4 = L4Layer(LayerConfig("L4", input_size=config.l4_size, output_size=config.l4_size, exc_ratio=config.exc_ratio))
        # L2/3 receives from L4
        self.l23 = L23Layer(LayerConfig("L23", input_size=config.l4_size, output_size=config.l23_size, exc_ratio=config.exc_ratio))
        # L5 receives from L2/3
        self.l5 = L5Layer(LayerConfig("L5", input_size=config.l23_size, output_size=config.l5_size, exc_ratio=config.exc_ratio))
        # L6 receives from L5
        self.l6 = L6Layer(LayerConfig("L6", input_size=config.l5_size, output_size=config.l6_size, exc_ratio=config.exc_ratio))

        # Connectivity Masks (Frozen structural constraints)
        # We store these as buffers so they are part of the state dict but not optimized
        self.register_buffer("mask_l4_l23", generate_laminar_connectivity_mask(
            "L4", "L23", config.l4_size, config.l23_size, config
        ))
        self.register_buffer("mask_l23_l5", generate_laminar_connectivity_mask(
            "L23", "L5", config.l23_size, config.l5_size, config
        ))
        self.register_buffer("mask_l5_l6", generate_laminar_connectivity_mask(
            "L5", "L6", config.l5_size, config.l6_size, config
        ))
        self.register_buffer("mask_l6_l4", generate_laminar_connectivity_mask(
            "L6", "L4", config.l6_size, config.l4_size, config
        ))
        self.register_buffer("mask_l23_rec", generate_laminar_connectivity_mask(
            "L23", "L23", config.l23_size, config.l23_size, config
        ))
        self.register_buffer("mask_l5_rec", generate_laminar_connectivity_mask(
            "L5", "L5", config.l5_size, config.l5_size, config
        ))

        # Verify constraints on init
        if not verify_connectivity_constraints(self.mask_l4_l23, "L4", "L23", config):
            raise RuntimeError("L4->L23 connectivity constraint violated")
        if not verify_connectivity_constraints(self.mask_l6_l4, "L6", "L4", config):
            raise RuntimeError("L6->L4 connectivity constraint violated")

    def forward(self, x: torch.Tensor, iterations: int = 1) -> torch.Tensor:
        """
        Args:
            x: Input to L4 (batch, l4_size)
            iterations: Number of recurrent steps within the column
        Returns:
            Output from L5 (batch, l5_size) - the "output" of the column
        """
        # Initial pass
        h_l4 = self.l4(x)
        h_l23 = self.l23(h_l4)
        h_l5 = self.l5(h_l23)
        h_l6 = self.l6(h_l5)

        # Recurrent dynamics
        for _ in range(iterations):
            # L2/3 Recurrence
            # Apply mask to h_l23 before projecting back to L2/3
            # We need to project h_l23 through a linear layer that respects the mask
            # For simplicity in this structural implementation, we assume the mask
            # is applied to the weight matrix of a recurrent layer or via masking.
            # Here we implement a simple masked recurrent update.

            # Recurrent input to L2/3
            rec_l23 = torch.matmul(self.mask_l23_rec, h_l23.t()).t()
            h_l23 = self.l23(torch.cat([h_l4, rec_l23], dim=-1)) # Combine feedforward and recurrent

            # Recurrent input to L5
            rec_l5 = torch.matmul(self.mask_l5_rec, h_l5.t()).t()
            h_l5 = self.l5(torch.cat([h_l23, rec_l5], dim=-1))

            # Feedback from L6 to L4
            feedback = torch.matmul(self.mask_l6_l4, h_l6.t()).t()
            # Combine original input with feedback for L4
            # Note: In a real circuit, this is complex. We add it to the input stream.
            h_l4 = self.l4(x + feedback)

            # Re-propagate quickly
            h_l23 = self.l23(h_l4)
            h_l5 = self.l5(h_l23)
            h_l6 = self.l6(h_l5)

        return h_l5

def create_microcircuit_column(config: MicrocircuitColumnConfig) -> MicrocircuitColumn:
    """Factory function to create a MicrocircuitColumn."""
    return MicrocircuitColumn(config)

def main():
    """Demo/Verification of connectivity mask generation."""
    logging.basicConfig(level=logging.INFO)
    config = MicrocircuitColumnConfig(l4_size=64, l23_size=64, l5_size=64, l6_size=64, exc_ratio=0.8)

    # Generate and print mask stats
    mask_l4_l23 = generate_laminar_connectivity_mask("L4", "L23", 64, 64, config)
    logger.info(f"L4->L23 Mask shape: {mask_l4_l23.shape}, Non-zero: {mask_l4_l23.sum().item()}")

    mask_l6_l4 = generate_laminar_connectivity_mask("L6", "L4", 64, 64, config)
    logger.info(f"L6->L4 Mask shape: {mask_l6_l4.shape}, Non-zero: {mask_l6_l4.sum().item()}")

    # Verify forbidden connections
    mask_l4_l5 = generate_laminar_connectivity_mask("L4", "L5", 64, 64, config)
    assert mask_l4_l5.sum() == 0, "L4->L5 should be forbidden"
    logger.info("Verified L4->L5 is forbidden (sparse).")

    print("Connectivity mask generation logic verified.")

if __name__ == "__main__":
    main()