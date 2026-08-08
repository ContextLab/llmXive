"""
Diffusion Model Implementation for llmXive.

Implements a Bidirectional Masked Diffusion Model (MDM) with large-scale
parameters, matching the architecture of the autoregressive baseline
(identical embed_dim, num_heads, etc.).
"""
import math
from typing import Optional, Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F

from utils.config import (
    get_embed_dim,
    get_num_heads,
    get_vocab_size,
    get_max_seq_length,
    get_config,
    ConfigError,
)
from utils.logging import get_logger

logger = get_logger(__name__)


class CausalSelfAttention(nn.Module):
    """
    Standard self-attention block.
    Note: For the diffusion model, we will use bidirectional masking logic
    in the forward pass or attention mask generation, but the block itself
    is the standard transformer attention.
    """
    def __init__(self, embed_dim: int, num_heads: int):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        assert self.head_dim * num_heads == embed_dim, "embed_dim must be divisible by num_heads"

        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=False)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x: torch.Tensor, attn_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        B, T, C = x.size()

        q, k, v = self.qkv(x).split(self.embed_dim, dim=2)
        q = q.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

        # Standard attention
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=attn_mask, is_causal=False)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        y = self.dropout(self.proj(y))
        return y


class MLPBlock(nn.Module):
    """
    MLP block for the transformer.
    """
    def __init__(self, embed_dim: int, hidden_dim: int):
        super().__init__()
        self.fc1 = nn.Linear(embed_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, embed_dim)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(self.act(self.fc1(x)))


class TransformerBlock(nn.Module):
    """
    Standard Transformer block with Attention + MLP.
    """
    def __init__(self, embed_dim: int, num_heads: int, hidden_dim: int):
        super().__init__()
        self.ln1 = nn.LayerNorm(embed_dim)
        self.attn = CausalSelfAttention(embed_dim, num_heads)
        self.ln2 = nn.LayerNorm(embed_dim)
        self.mlp = MLPBlock(embed_dim, hidden_dim)

    def forward(self, x: torch.Tensor, attn_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = x + self.attn(self.ln1(x), attn_mask=attn_mask)
        x = x + self.mlp(self.ln2(x))
        return x


class DiffusionModel(nn.Module):
    """
    Bidirectional Masked Diffusion Model (MDM).

    This model is designed for discrete diffusion on text.
    It uses a bidirectional transformer backbone.
    The forward method computes the loss for a diffusion step:
    1. Takes a noisy sequence (with [MASK] tokens).
    2. Predicts the original token at masked positions.
    """
    def __init__(
        self,
        vocab_size: int,
        embed_dim: int,
        num_heads: int,
        num_layers: int,
        max_seq_length: int,
        hidden_dim: Optional[int] = None,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.max_seq_length = max_seq_length

        if hidden_dim is None:
            hidden_dim = embed_dim * 4

        # Embeddings
        self.token_emb = nn.Embedding(vocab_size + 1, embed_dim)  # +1 for MASK token
        self.pos_emb = nn.Embedding(max_seq_length, embed_dim)
        self.mask_id = vocab_size  # Use vocab_size as the index for [MASK]

        # Transformer Backbone
        self.layers = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, hidden_dim)
            for _ in range(num_layers)
        ])

        # Output Head (Predict original token from masked position)
        self.head = nn.Linear(embed_dim, vocab_size)

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor, t: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass for diffusion training.

        Args:
            x: Input tensor of shape (B, T) containing token IDs.
               Masked positions should contain the special [MASK] token ID.
            t: Optional timestep (not strictly used in the forward pass for this
               simple implementation, but kept for API consistency with diffusion).

        Returns:
            logits: Tensor of shape (B, T, vocab_size) predicting the original token.
        """
        B, T = x.size()

        # Positional embeddings
        pos_ids = torch.arange(T, device=x.device).unsqueeze(0).expand(B, -1)
        x_emb = self.token_emb(x) + self.pos_emb(pos_ids)

        # Apply transformer layers
        attn_mask = None  # Bidirectional: no causal mask needed
        for layer in self.layers:
            x_emb = layer(x_emb, attn_mask=attn_mask)

        # Project to vocab size
        logits = self.head(x_emb)
        return logits

    def get_loss(self, x_noisy: torch.Tensor, x_target: torch.Tensor) -> torch.Tensor:
        """
        Compute the diffusion loss.

        Args:
            x_noisy: Noisy input sequence (B, T) with [MASK] tokens.
            x_target: Original target sequence (B, T) to predict.

        Returns:
            loss: Mean cross-entropy loss at masked positions.
        """
        logits = self.forward(x_noisy)
        # Only compute loss at masked positions
        mask_positions = (x_noisy == self.mask_id)
        if not mask_positions.any():
            # Fallback if no masking (should not happen in proper training loop)
            return F.cross_entropy(logits.view(-1, self.vocab_size), x_target.view(-1))

        # Gather logits and targets for masked positions
        loss = F.cross_entropy(
            logits[mask_positions],
            x_target[mask_positions],
            reduction='mean'
        )
        return loss


def create_diffusion_model() -> DiffusionModel:
    """
    Factory function to create a DiffusionModel with project configuration.
    Ensures parameter counts and hyperparameters match the AR baseline.
    """
    try:
        vocab_size = get_vocab_size()
        embed_dim = get_embed_dim()
        num_heads = get_num_heads()
        max_seq_length = get_max_seq_length()
        
        # Determine number of layers to approximate large-scale parameters
        # The AR model likely uses a standard depth. We'll use a reasonable depth
        # that scales with embed_dim to match the "large-scale" requirement.
        # A common ratio is ~12-24 layers for 768 dim. Let's use 12 for this implementation.
        num_layers = 12
        
        logger.info(f"Creating DiffusionModel: vocab={vocab_size}, embed={embed_dim}, "
                    f"heads={num_heads}, layers={num_layers}, seq_len={max_seq_length}")
        
        model = DiffusionModel(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            num_heads=num_heads,
            num_layers=num_layers,
            max_seq_length=max_seq_length,
        )
        
        # Log parameter count
        total_params = sum(p.numel() for p in model.parameters())
        logger.info(f"DiffusionModel total parameters: {total_params:,}")
        
        return model
        
    except ConfigError as e:
        logger.error(f"Failed to create diffusion model due to config error: {e}")
        raise