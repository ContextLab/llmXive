"""
Baseline Transformer implementation for cortical column comparison.

Implements standard Transformer MLP and Attention layers to serve as a
computational universal baseline against which the microcircuit model
will be compared.

This module provides:
- MultiHeadAttention: Standard scaled-dot product attention
- FeedForward: Standard Transformer MLP block
- TransformerBlock: Combined attention + FFN with residual connections
- BaselineTransformer: Full encoder-only transformer model
"""

import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiHeadAttention(nn.Module):
    """
    Standard multi-head scaled-dot product attention mechanism.

    Implements the attention function from "Attention Is All You Need":
    Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        dropout: float = 0.1,
        bias: bool = True,
    ):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        # Linear projections for Q, K, V
        self.w_q = nn.Linear(d_model, d_model, bias=bias)
        self.w_k = nn.Linear(d_model, d_model, bias=bias)
        self.w_v = nn.Linear(d_model, d_model, bias=bias)

        # Output projection
        self.w_o = nn.Linear(d_model, d_model, bias=bias)

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass through multi-head attention.

        Args:
            query: Query tensor of shape (batch, seq_len, d_model)
            key: Key tensor of shape (batch, seq_len, d_model)
            value: Value tensor of shape (batch, seq_len, d_model)
            mask: Optional attention mask of shape (batch, 1, 1, seq_len)
                  or (1, 1, seq_len, seq_len) for causal masking

        Returns:
            Output tensor of shape (batch, seq_len, d_model)
        """
        batch_size, seq_len, _ = query.size()

        # Project Q, K, V
        q = self.w_q(query).view(batch_size, seq_len, self.n_heads, self.d_k)
        k = self.w_k(key).view(batch_size, seq_len, self.n_heads, self.d_k)
        v = self.w_v(value).view(batch_size, seq_len, self.n_heads, self.d_k)

        # Transpose for multi-head: (batch, n_heads, seq_len, d_k)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)

        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Apply attention to values
        output = torch.matmul(attn_weights, v)

        # Reshape and project back
        output = output.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.d_model
        )

        return self.w_o(output)


class FeedForward(nn.Module):
    """
    Standard Transformer feed-forward network (MLP).

    Consists of two linear transformations with a ReLU activation in between:
    FFN(x) = max(0, xW1 + b1)W2 + b2
    """

    def __init__(
        self,
        d_model: int,
        d_ff: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the feed-forward network.

        Args:
            x: Input tensor of shape (batch, seq_len, d_model)

        Returns:
            Output tensor of shape (batch, seq_len, d_model)
        """
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


class TransformerBlock(nn.Module):
    """
    A single Transformer block containing multi-head attention and feed-forward layers.

    Implements the standard residual connections and layer normalization:
    - LayerNorm(x + MultiHeadAttention(LayerNorm(x)))
    - LayerNorm(x + FFN(LayerNorm(x)))
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        d_ff: int,
        dropout: float = 0.1,
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
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass through the transformer block.

        Args:
            x: Input tensor of shape (batch, seq_len, d_model)
            mask: Optional attention mask

        Returns:
            Output tensor of shape (batch, seq_len, d_model)
        """
        # Self-attention with residual connection
        attn_out = self.attention(self.norm1(x), self.norm1(x), self.norm1(x), mask)
        x = x + self.dropout(attn_out)

        # Feed-forward with residual connection
        ff_out = self.feed_forward(self.norm2(x))
        x = x + self.dropout(ff_out)

        return x


class BaselineTransformer(nn.Module):
    """
    Complete baseline Transformer model for sequence modeling.

    This model serves as the computational universal baseline against which
    the cortical column microcircuit will be compared. It implements a standard
    encoder-only Transformer architecture.

    Args:
        d_model: Dimensionality of the model (default: 256)
        n_heads: Number of attention heads (default: 8)
        n_layers: Number of transformer blocks (default: 4)
        d_ff: Dimensionality of feed-forward network (default: 1024)
        dropout: Dropout rate (default: 0.1)
        max_seq_len: Maximum sequence length for positional encoding (default: 512)
        vocab_size: Vocabulary size for embedding layer (default: 1000)
    """

    def __init__(
        self,
        d_model: int = 256,
        n_heads: int = 8,
        n_layers: int = 4,
        d_ff: int = 1024,
        dropout: float = 0.1,
        max_seq_len: int = 512,
        vocab_size: int = 1000,
        use_positional_encoding: bool = True,
    ):
        super().__init__()

        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.use_positional_encoding = use_positional_encoding

        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, d_model)

        # Positional encoding (sinusoidal)
        if use_positional_encoding:
            self.register_buffer(
                "pos_encoding",
                self._create_positional_encoding(max_seq_len, d_model),
            )

        # Transformer blocks
        self.blocks = nn.ModuleList(
            [
                TransformerBlock(d_model, n_heads, d_ff, dropout)
                for _ in range(n_layers)
            ]
        )

        # Final layer normalization
        self.norm = nn.LayerNorm(d_model)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    @staticmethod
    def _create_positional_encoding(max_len: int, d_model: int) -> torch.Tensor:
        """
        Create sinusoidal positional encodings.

        Args:
            max_len: Maximum sequence length
            d_model: Dimensionality of the model

        Returns:
            Positional encoding tensor of shape (max_len, d_model)
        """
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        return pe.unsqueeze(0)  # (1, max_len, d_model)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass through the baseline transformer.

        Args:
            x: Input tensor of shape (batch, seq_len) containing token indices
            mask: Optional attention mask of shape (batch, 1, 1, seq_len)

        Returns:
            Output tensor of shape (batch, seq_len, d_model)
        """
        batch_size, seq_len = x.size()

        # Embedding
        x = self.embedding(x) * math.sqrt(self.d_model)

        # Add positional encoding
        if self.use_positional_encoding:
            # Ensure we don't exceed max_seq_len
            if seq_len > self.max_seq_len:
                raise ValueError(
                    f"Sequence length {seq_len} exceeds max_seq_len {self.max_seq_len}"
                )
            x = x + self.pos_encoding[:, :seq_len, :]

        x = self.dropout(x)

        # Pass through transformer blocks
        for block in self.blocks:
            x = block(x, mask)

        # Final layer normalization
        x = self.norm(x)

        return x

    def get_num_parameters(self) -> int:
        """Return the total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters())

    def get_parameter_breakdown(self) -> dict:
        """Return a breakdown of parameters by component."""
        breakdown = {}
        breakdown["embedding"] = sum(
            p.numel() for n, p in self.named_parameters() if "embedding" in n
        )
        breakdown["attention"] = sum(
            p.numel()
            for n, p in self.named_parameters()
            if "attention" in n and "w_o" not in n
        )
        breakdown["output_projection"] = sum(
            p.numel() for n, p in self.named_parameters() if "w_o" in n
        )
        breakdown["feed_forward"] = sum(
            p.numel() for n, p in self.named_parameters() if "feed_forward" in n
        )
        breakdown["layer_norms"] = sum(
            p.numel() for n, p in self.named_parameters() if "norm" in n
        )
        breakdown["total"] = self.get_num_parameters()
        return breakdown