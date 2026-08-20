"""
Baseline Transformer implementation for US1.
Implements standard Transformer MLP and Attention layers.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List
import math
import logging

logger = logging.getLogger(__name__)


class PositionalEncoding(nn.Module):
    """Standard sinusoidal positional encoding."""

    def __init__(self, d_model: int, max_seq_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Create positional encoding matrix
        pe = torch.zeros(max_seq_len, d_model)
        position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # Shape: (1, max_seq_len, d_model)

        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, d_model)
        Returns:
            Tensor with positional encoding added and dropout applied.
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class MultiHeadAttention(nn.Module):
    """Multi-head self-attention mechanism."""

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(p=dropout)

    def forward(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            q, k, v: Input tensors of shape (batch_size, seq_len, d_model)
            mask: Optional attention mask of shape (batch_size, 1, 1, seq_len) or
                  (batch_size, n_heads, seq_len, seq_len)
        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        batch_size = q.size(0)

        # Linear projections and split into heads
        Q = self.w_q(q).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = self.w_k(k).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.w_v(v).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)

        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        context = torch.matmul(attn_weights, V)

        # Concatenate heads
        context = context.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model
        )

        # Final linear projection
        output = self.w_o(context)
        return output


class FeedForward(nn.Module):
    """Position-wise feed-forward network (FFN)."""

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        x = self.linear1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.linear2(x)
        return x


class TransformerBlock(nn.Module):
    """Single Transformer block with multi-head attention and FFN."""

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

        self.dropout = nn.Dropout(p=dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
            mask: Optional attention mask
        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        # Multi-head attention with residual and layer norm
        attn_out = self.attention(x, x, x, mask=mask)
        x = self.norm1(x + self.dropout(attn_out))

        # Feed-forward with residual and layer norm
        ff_out = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_out))

        return x


class BaselineTransformer(nn.Module):
    """
    Standard Transformer encoder for baseline comparison.
    Designed for synthetic function approximation tasks.
    """

    def __init__(
        self,
        d_model: int = 256,
        n_heads: int = 8,
        n_layers: int = 6,
        d_ff: int = 1024,
        max_seq_len: int = 512,
        input_dim: int = 1,
        output_dim: int = 1,
        dropout: float = 0.1
    ):
        super().__init__()

        self.d_model = d_model
        self.input_dim = input_dim
        self.output_dim = output_dim

        # Input projection
        self.input_projection = nn.Linear(input_dim, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len, dropout)

        # Transformer encoder layers
        self.layers = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])

        # Output projection
        self.output_projection = nn.Linear(d_model, output_dim)

        self.dropout = nn.Dropout(p=dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)
            mask: Optional attention mask
        Returns:
            Output tensor of shape (batch_size, seq_len, output_dim)
        """
        # Project input to d_model dimension
        x = self.input_projection(x)
        x = self.pos_encoder(x)
        x = self.dropout(x)

        # Pass through transformer layers
        for layer in self.layers:
            x = layer(x, mask=mask)

        # Project to output dimension
        output = self.output_projection(x)
        return output


def create_baseline_transformer(
    d_model: int = 256,
    n_heads: int = 8,
    n_layers: int = 6,
    d_ff: int = 1024,
    max_seq_len: int = 512,
    input_dim: int = 1,
    output_dim: int = 1,
    dropout: float = 0.1
) -> BaselineTransformer:
    """
    Factory function to create a BaselineTransformer model.

    Args:
        d_model: Dimension of model (embedding size)
        n_heads: Number of attention heads
        n_layers: Number of transformer layers
        d_ff: Dimension of feed-forward network
        max_seq_len: Maximum sequence length
        input_dim: Dimension of input features
        output_dim: Dimension of output features
        dropout: Dropout rate

    Returns:
        Configured BaselineTransformer instance
    """
    logger.info(
        f"Creating BaselineTransformer: d_model={d_model}, "
        f"n_heads={n_heads}, n_layers={n_layers}, d_ff={d_ff}"
    )
    return BaselineTransformer(
        d_model=d_model,
        n_heads=n_heads,
        n_layers=n_layers,
        d_ff=d_ff,
        max_seq_len=max_seq_len,
        input_dim=input_dim,
        output_dim=output_dim,
        dropout=dropout
    )


def count_parameters(model: nn.Module) -> int:
    """Count total number of parameters in a model."""
    return sum(p.numel() for p in model.parameters())


def main():
    """
    Simple test to verify the model can be instantiated and run.
    """
    # Create model
    model = create_baseline_transformer(
        d_model=128,
        n_heads=4,
        n_layers=2,
        d_ff=512,
        input_dim=1,
        output_dim=1
    )

    # Count parameters
    total_params = count_parameters(model)
    print(f"Total parameters: {total_params:,}")

    # Run a dummy forward pass
    batch_size = 4
    seq_len = 64
    dummy_input = torch.randn(batch_size, seq_len, 1)

    with torch.no_grad():
        output = model(dummy_input)

    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print("BaselineTransformer implementation verified successfully.")


if __name__ == "__main__":
    main()