"""
Baseline Transformer implementation for computational universality comparison.

This module provides a standard Transformer architecture with self-attention
and MLP layers, serving as a control baseline for the cortical column microcircuit.
Implements standard attention mechanisms without biological constraints.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


class FeedForward(nn.Module):
    """Standard Transformer MLP layer."""

    def __init__(
        self,
        d_model: int,
        d_ff: int,
        dropout: float = 0.1
    ):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        self.activation = F.relu

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear2(self.dropout(self.activation(self.linear1(x))))


class MultiHeadAttention(nn.Module):
    """Standard multi-head self-attention mechanism."""

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        dropout: float = 0.1,
        bias: bool = True
    ):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.w_q = nn.Linear(d_model, d_model, bias=bias)
        self.w_k = nn.Linear(d_model, d_model, bias=bias)
        self.w_v = nn.Linear(d_model, d_model, bias=bias)
        self.w_o = nn.Linear(d_model, d_model, bias=bias)

        self.dropout = nn.Dropout(dropout)
        self.scale = self.d_k ** -0.5

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        batch_size = query.size(0)

        # Linear projections and split heads
        q = self.w_q(query).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        k = self.w_k(key).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        v = self.w_v(value).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale

        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        # Apply attention to values
        out = torch.matmul(attn, v)

        # Concatenate heads
        out = out.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model
        )

        return self.w_o(out)


class TransformerBlock(nn.Module):
    """Single Transformer layer with attention and MLP."""

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        d_ff: int,
        dropout: float = 0.1
    ):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, n_heads, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        # Self-attention with residual connection
        attn_out = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_out))

        # MLP with residual connection
        ff_out = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_out))

        return x


class BaselineTransformer(nn.Module):
    """
    Standard Transformer model for baseline comparison.

    This model implements the canonical Transformer architecture with
    self-attention and feed-forward layers, serving as a computational
    baseline against which the cortical column microcircuit will be compared.
    """

    def __init__(
        self,
        d_model: int = 256,
        n_heads: int = 8,
        n_layers: int = 6,
        d_ff: int = 1024,
        dropout: float = 0.1,
        input_dim: int = 512,
        output_dim: int = 512,
        max_seq_len: int = 512
    ):
        super().__init__()

        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff

        # Input projection
        self.input_projection = nn.Linear(input_dim, d_model)

        # Positional encoding (learned)
        self.positional_encoding = nn.Parameter(
            torch.zeros(1, max_seq_len, d_model)
        )

        # Transformer layers
        self.layers = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])

        # Output projection
        self.output_projection = nn.Linear(d_model, output_dim)

        self.dropout = nn.Dropout(dropout)
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with Xavier uniform distribution."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass through the Transformer.

        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)
            mask: Optional attention mask of shape (batch_size, seq_len, seq_len)

        Returns:
            Output tensor of shape (batch_size, seq_len, output_dim)
        """
        # Project input to model dimension
        x = self.input_projection(x) * (self.d_model ** 0.5)
        x = x + self.positional_encoding[:, :x.size(1), :]
        x = self.dropout(x)

        # Pass through transformer layers
        for layer in self.layers:
            x = layer(x, mask)

        # Project to output dimension
        return self.output_projection(x)

    def get_num_parameters(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters())

    def get_num_trainable_parameters(self) -> int:
        """Return number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def create_baseline_transformer(
    d_model: int = 256,
    n_heads: int = 8,
    n_layers: int = 6,
    d_ff: int = 1024,
    dropout: float = 0.1,
    input_dim: int = 512,
    output_dim: int = 512,
    max_seq_len: int = 512
) -> BaselineTransformer:
    """
    Factory function to create a BaselineTransformer instance.

    Args:
        d_model: Dimension of the model (embedding size)
        n_heads: Number of attention heads
        n_layers: Number of transformer layers
        d_ff: Dimension of feed-forward network
        dropout: Dropout probability
        input_dim: Dimension of input features
        output_dim: Dimension of output features
        max_seq_len: Maximum sequence length

    Returns:
        Configured BaselineTransformer instance
    """
    return BaselineTransformer(
        d_model=d_model,
        n_heads=n_heads,
        n_layers=n_layers,
        d_ff=d_ff,
        dropout=dropout,
        input_dim=input_dim,
        output_dim=output_dim,
        max_seq_len=max_seq_len
    )
