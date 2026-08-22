"""
Baseline Transformer implementation for universal function approximation.

Implements standard Transformer architecture with:
- Multi-head self-attention
- Position-wise feed-forward networks
- Layer normalization
- Positional encoding

This serves as the control baseline for comparing against the cortical column microcircuit.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List
import math
import logging

logger = logging.getLogger(__name__)


class PositionalEncoding(nn.Module):
    """
    Standard sinusoidal positional encoding for Transformer models.
    
    Args:
        d_model: Dimensionality of the model
        max_len: Maximum sequence length to encode
        dropout: Dropout probability
    """
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # Create positional encoding matrix
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Add positional encoding to input tensor.
        
        Args:
            x: Input tensor of shape (seq_len, batch_size, d_model)
        
        Returns:
            Tensor with positional encoding added
        """
        x = x + self.pe[:x.size(0), :, :]
        return self.dropout(x)


class MultiHeadAttention(nn.Module):
    """
    Multi-head self-attention mechanism.
    
    Args:
        d_model: Model dimension
        num_heads: Number of attention heads
        dropout: Dropout probability
    """
    def __init__(self, d_model: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(p=dropout)
        self.scale = math.sqrt(self.d_k)
    
    def forward(
        self, 
        query: torch.Tensor, 
        key: torch.Tensor, 
        value: torch.Tensor, 
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute multi-head attention.
        
        Args:
            query: Query tensor (seq_len, batch_size, d_model)
            key: Key tensor (seq_len, batch_size, d_model)
            value: Value tensor (seq_len, batch_size, d_model)
            mask: Optional attention mask
        
        Returns:
            Attended output tensor
        """
        batch_size = query.size(1)
        
        # Linear projections and split heads
        q = self.w_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        k = self.w_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        v = self.w_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # Compute attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) / self.scale
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        # Apply softmax and dropout
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        attn_output = torch.matmul(attn_weights, v)
        
        # Concatenate heads
        attn_output = attn_output.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model
        )
        
        # Final linear projection
        output = self.w_o(attn_output)
        
        return output


class FeedForward(nn.Module):
    """
    Position-wise feed-forward network.
    
    Args:
        d_model: Model dimension
        d_ff: Hidden layer dimension (typically 4 * d_model)
        dropout: Dropout probability
    """
    def __init__(self, d_model: int, d_ff: int = 2048, dropout: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(p=dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply feed-forward network.
        
        Args:
            x: Input tensor (seq_len, batch_size, d_model)
        
        Returns:
            Output tensor after FFN
        """
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


class TransformerBlock(nn.Module):
    """
    Single Transformer encoder block with attention and feed-forward.
    
    Args:
        d_model: Model dimension
        num_heads: Number of attention heads
        d_ff: Feed-forward hidden dimension
        dropout: Dropout probability
    """
    def __init__(
        self, 
        d_model: int, 
        num_heads: int = 8, 
        d_ff: int = 2048, 
        dropout: float = 0.1
    ):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
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
        Apply transformer block with residual connections.
        
        Args:
            x: Input tensor (seq_len, batch_size, d_model)
            mask: Optional attention mask
        
        Returns:
            Output tensor after transformer block
        """
        # Self-attention with residual
        attn_out = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_out))
        
        # Feed-forward with residual
        ff_out = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_out))
        
        return x


class BaselineTransformer(nn.Module):
    """
    Complete baseline Transformer model for sequence-to-sequence or 
    sequence-to-vector tasks.
    
    This model serves as the control baseline for comparison with 
    the cortical column microcircuit architecture.
    
    Args:
        d_model: Model dimension
        num_layers: Number of transformer blocks
        num_heads: Number of attention heads
        d_ff: Feed-forward hidden dimension
        max_seq_len: Maximum sequence length
        dropout: Dropout probability
        output_dim: Output dimension (for regression/classification)
    """
    def __init__(
        self,
        d_model: int = 512,
        num_layers: int = 6,
        num_heads: int = 8,
        d_ff: int = 2048,
        max_seq_len: int = 5000,
        dropout: float = 0.1,
        output_dim: Optional[int] = None
    ):
        super().__init__()
        
        self.d_model = d_model
        self.num_layers = num_layers
        self.output_dim = output_dim
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len, dropout)
        
        # Transformer blocks
        self.layers = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        
        # Final projection (if output_dim specified)
        if output_dim is not None:
            self.output_projection = nn.Linear(d_model, output_dim)
        else:
            self.output_projection = None
        
        self.init_weights()
    
    def init_weights(self):
        """Initialize weights with Xavier initialization."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(
        self, 
        x: torch.Tensor, 
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass through the transformer.
        
        Args:
            x: Input tensor of shape (seq_len, batch_size, d_model)
            mask: Optional attention mask
        
        Returns:
            Output tensor. If output_dim is specified, returns (batch_size, output_dim).
            Otherwise returns (seq_len, batch_size, d_model).
        """
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Pass through transformer layers
        for layer in self.layers:
            x = layer(x, mask)
        
        # Aggregate over sequence dimension (mean pooling)
        x = x.mean(dim=0)  # (batch_size, d_model)
        
        # Project to output dimension if specified
        if self.output_projection is not None:
            x = self.output_projection(x)
        
        return x


def create_baseline_transformer(
    d_model: int = 512,
    num_layers: int = 6,
    num_heads: int = 8,
    d_ff: int = 2048,
    max_seq_len: int = 5000,
    dropout: float = 0.1,
    output_dim: Optional[int] = None
) -> BaselineTransformer:
    """
    Factory function to create a baseline Transformer model.
    
    Args:
        d_model: Model dimension
        num_layers: Number of transformer blocks
        num_heads: Number of attention heads
        d_ff: Feed-forward hidden dimension
        max_seq_len: Maximum sequence length
        dropout: Dropout probability
        output_dim: Output dimension (optional)
    
    Returns:
        Configured BaselineTransformer instance
    """
    logger.info(f"Creating baseline Transformer: d_model={d_model}, "
               f"num_layers={num_layers}, num_heads={num_heads}")
    
    model = BaselineTransformer(
        d_model=d_model,
        num_layers=num_layers,
        num_heads=num_heads,
        d_ff=d_ff,
        max_seq_len=max_seq_len,
        dropout=dropout,
        output_dim=output_dim
    )
    
    logger.info(f"Model created with {count_parameters(model):,} parameters")
    return model


def count_parameters(model: nn.Module) -> int:
    """
    Count total number of trainable parameters in a model.
    
    Args:
        model: PyTorch model
    
    Returns:
        Total number of trainable parameters
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def main():
    """
    Simple demonstration of the baseline Transformer.
    Creates a model, runs a forward pass, and logs parameter count.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create model
    model = create_baseline_transformer(
        d_model=256,
        num_layers=4,
        num_heads=8,
        d_ff=1024,
        output_dim=1  # For regression
    )
    
    # Create dummy input
    batch_size = 4
    seq_len = 100
    d_model = 256
    
    x = torch.randn(seq_len, batch_size, d_model)
    
    # Forward pass
    output = model(x)
    
    logger.info(f"Input shape: {x.shape}")
    logger.info(f"Output shape: {output.shape}")
    logger.info(f"Total parameters: {count_parameters(model):,}")
    
    # Verify output dimension
    assert output.shape == (batch_size, 1), f"Expected output shape (batch_size, 1), got {output.shape}"
    
    logger.info("Baseline Transformer demo completed successfully")


if __name__ == "__main__":
    main()