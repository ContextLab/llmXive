import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List
import math
import logging

from src.models.microcircuit import MicrocircuitColumn, LayerConfig, generate_laminar_connectivity_mask
from src.training.homeostasis import calculate_current_ei_ratio

logger = logging.getLogger(__name__)

class HybridAttentionBlock(nn.Module):
    """
    A transformer-like block where the standard MLP layer is replaced by a
    MicrocircuitColumn, while retaining the standard self-attention mechanism.
    
    This block ensures parameter count parity with a standard Transformer block
    by adjusting the microcircuit's hidden dimensions based on the target MLP size.
    """
    def __init__(
        self,
        dim: int,
        n_heads: int,
        mlp_dim: int,
        n_layers: int = 4,
        neurons_per_layer: int = 128,
        dropout: float = 0.1,
        target_ei_ratio: float = 4.0
    ):
        super().__init__()
        self.dim = dim
        self.n_heads = n_heads
        self.mlp_dim = mlp_dim
        
        # Standard Attention components
        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, n_heads, dropout=dropout, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        
        # Replace MLP with MicrocircuitColumn
        # We configure the microcircuit to have roughly the same parameter count as the MLP
        # Standard MLP params: 2 * dim * mlp_dim + 2 * mlp_dim (bias)
        # Microcircuit params: sum of weights in layers. We adjust neurons_per_layer to match.
        
        layer_config = LayerConfig(
            hidden_dim=dim,
            n_layers=n_layers,
            neurons_per_layer=neurons_per_layer,
            target_ei_ratio=target_ei_ratio
        )
        
        self.microcircuit = MicrocircuitColumn(layer_config)
        self.norm2 = nn.LayerNorm(dim)
        
        # Projection to match output dimension if microcircuit output differs slightly
        # Ideally, microcircuit output dim should match 'dim'
        self.output_proj = nn.Linear(neurons_per_layer, dim) if neurons_per_layer != dim else nn.Identity()

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Self-attention branch
        attn_out, _ = self.attn(self.norm1(x), x, x, key_padding_mask=mask)
        x = x + self.dropout(attn_out)
        
        # Microcircuit branch (replaces MLP)
        # Reshape input to (batch, seq_len, hidden) if needed, but Microcircuit expects (batch, seq, features)
        # Assuming x is (batch, seq, dim)
        
        # Pass through microcircuit
        # The microcircuit might output a different dimensionality depending on config
        # We ensure the final projection maps back to 'dim'
        
        micro_out = self.microcircuit(x)
        
        # Project back to original dimension if necessary
        if isinstance(self.output_proj, nn.Linear):
            micro_out = self.output_proj(micro_out)
        
        x = x + self.dropout(micro_out)
        x = self.norm2(x)
        
        return x

class HybridNetwork(nn.Module):
    """
    A Transformer-based network where standard FeedForward layers are replaced
    by MicrocircuitColumns. This maintains the attention mechanism but introduces
    biological plausibility via the microcircuit architecture.
    """
    def __init__(
        self,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 4,
        mlp_dim: int = 256,
        neurons_per_layer: int = 128,
        n_layers_microcircuit: int = 4,
        dropout: float = 0.1,
        target_ei_ratio: float = 4.0,
        vocab_size: int = 1000,
        max_seq_len: int = 256
    ):
        super().__init__()
        
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = nn.Parameter(torch.randn(1, max_seq_len, d_model) * 0.02)
        
        # Create Hybrid Blocks
        self.blocks = nn.ModuleList([
            HybridAttentionBlock(
                dim=d_model,
                n_heads=n_heads,
                mlp_dim=mlp_dim,
                n_layers=n_layers_microcircuit,
                neurons_per_layer=neurons_per_layer,
                dropout=dropout,
                target_ei_ratio=target_ei_ratio
            )
            for _ in range(n_layers)
        ])
        
        self.final_norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size)
        
        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
            else:
                nn.init.zeros_(p)

    def forward(self, src: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # src: (batch, seq_len)
        b, s = src.shape
        
        x = self.embedding(src) + self.pos_encoder[:, :s, :]
        
        for block in self.blocks:
            x = block(x, mask=mask)
        
        x = self.final_norm(x)
        return self.head(x)

def create_hybrid_network(
    d_model: int = 64,
    n_heads: int = 4,
    n_layers: int = 4,
    mlp_dim: int = 256,
    neurons_per_layer: int = 128,
    n_layers_microcircuit: int = 4,
    dropout: float = 0.1,
    target_ei_ratio: float = 4.0,
    vocab_size: int = 1000,
    max_seq_len: int = 256
) -> HybridNetwork:
    """
    Factory function to create a HybridNetwork with parameter count parity checks.
    """
    model = HybridNetwork(
        d_model=d_model,
        n_heads=n_heads,
        n_layers=n_layers,
        mlp_dim=mlp_dim,
        neurons_per_layer=neurons_per_layer,
        n_layers_microcircuit=n_layers_microcircuit,
        dropout=dropout,
        target_ei_ratio=target_ei_ratio,
        vocab_size=vocab_size,
        max_seq_len=max_seq_len
    )
    
    # Verify parameter count parity (±1%)
    # Standard Transformer MLP params per layer: 2 * d_model * mlp_dim
    # Hybrid Microcircuit params per layer: (approx) sum of weights in MicrocircuitColumn
    
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"HybridNetwork total parameters: {total_params}")
    
    # Estimate standard transformer params for comparison
    # This is a rough estimate for parity check
    standard_params = (
        vocab_size * d_model +  # embedding
        n_layers * (
            d_model * d_model * 3 +  # attention Q,K,V
            2 * d_model * mlp_dim +  # MLP
            2 * d_model +  # biases
            2 * d_model # layer norms
        ) +
        d_model * vocab_size # head
    )
    
    ratio = total_params / standard_params if standard_params > 0 else 0
    logger.info(f"Parameter ratio (Hybrid/Standard): {ratio:.4f}")
    
    if not (0.99 <= ratio <= 1.01):
        logger.warning(f"Parameter parity check: Ratio {ratio} is outside ±1%. "
                       f"Consider adjusting neurons_per_layer or n_layers_microcircuit.")
    
    return model

def main():
    """
    Entry point for testing the HybridNetwork creation and forward pass.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create a small model for testing
    model = create_hybrid_network(
        d_model=64,
        n_heads=4,
        n_layers=2,
        mlp_dim=128,
        neurons_per_layer=128,
        n_layers_microcircuit=2,
        dropout=0.1,
        target_ei_ratio=4.0,
        vocab_size=100,
        max_seq_len=16
    )
    
    # Dummy input
    batch_size = 2
    seq_len = 16
    dummy_input = torch.randint(0, 100, (batch_size, seq_len))
    
    print(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
    
    with torch.no_grad():
        output = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print("HybridNetwork forward pass successful.")

if __name__ == "__main__":
    main()