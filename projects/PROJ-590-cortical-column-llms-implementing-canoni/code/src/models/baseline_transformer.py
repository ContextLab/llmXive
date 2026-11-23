"""
Baseline Transformer implementation for US1.
Implements standard Transformer MLP/Attention layers to serve as a computational
universal baseline for comparison against the cortical column microcircuit.
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
    Standard sinusoidal positional encoding.
    """
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model % 2 != 0:
            div_term = torch.exp(torch.arange(1, d_model, 2).float() * (-math.log(10000.0) / d_model))
            pe[:, 1::2] = torch.sin(position * div_term)
        else:
            pe[:, 1::2] = torch.cos(position * div_term)
        
        pe = pe.unsqueeze(0) # Shape: (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, d_model)
        Returns:
            Tensor of shape (batch_size, seq_len, d_model) with positional encoding added
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class MultiHeadAttention(nn.Module):
    """
    Standard Multi-Head Self-Attention mechanism.
    """
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
        self.scale = math.sqrt(self.d_k)

    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor, 
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            query: (batch_size, seq_len_q, d_model)
            key: (batch_size, seq_len_k, d_model)
            value: (batch_size, seq_len_k, d_model)
            mask: (batch_size, 1, 1, seq_len_k) or (batch_size, n_heads, seq_len_q, seq_len_k)
        Returns:
            (batch_size, seq_len_q, d_model)
        """
        batch_size = query.size(0)

        Q = self.w_q(query).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = self.w_k(key).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.w_v(value).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale

        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        context = torch.matmul(attn_weights, V)
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        
        output = self.w_o(context)
        return output


class FeedForward(nn.Module):
    """
    Position-wise Feed-Forward Network (MLP) within a Transformer block.
    """
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


class TransformerBlock(nn.Module):
    """
    A single Transformer block containing Multi-Head Attention and Feed-Forward layers
    with residual connections and layer normalization.
    """
    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, n_heads, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout)
        
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Self-Attention with residual and norm
        attn_out = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_out))
        
        # Feed-Forward with residual and norm
        ff_out = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_out))
        
        return x


class BaselineTransformer(nn.Module):
    """
    Full Baseline Transformer model for time-series prediction / function approximation.
    Composed of an input projection, positional encoding, N Transformer blocks, 
    and an output projection.
    """
    def __init__(self, input_dim: int, d_model: int, n_heads: int, n_layers: int, 
                 d_ff: int, output_dim: int, max_len: int = 500, dropout: float = 0.1):
        super().__init__()
        
        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len, dropout)
        
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff, dropout) 
            for _ in range(n_layers)
        ])
        
        self.output_proj = nn.Linear(d_model, output_dim)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: (batch_size, seq_len, input_dim)
            mask: Optional attention mask
        Returns:
            (batch_size, seq_len, output_dim)
        """
        x = self.input_proj(x)
        x = self.pos_encoder(x)
        
        for block in self.transformer_blocks:
            x = block(x, mask)
        
        x = self.dropout(x)
        return self.output_proj(x)


def create_baseline_transformer(
    input_dim: int, 
    output_dim: int, 
    d_model: int = 128, 
    n_heads: int = 4, 
    n_layers: int = 2, 
    d_ff: int = 256, 
    dropout: float = 0.1
) -> BaselineTransformer:
    """
    Factory function to create a BaselineTransformer with default hyperparameters.
    """
    logger.info(f"Creating BaselineTransformer: d_model={d_model}, n_heads={n_heads}, n_layers={n_layers}")
    return BaselineTransformer(
        input_dim=input_dim,
        output_dim=output_dim,
        d_model=d_model,
        n_heads=n_heads,
        n_layers=n_layers,
        d_ff=d_ff,
        dropout=dropout
    )


def count_parameters(model: nn.Module) -> int:
    """
    Count the number of trainable parameters in a model.
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def main():
    """
    CLI entry point for testing the BaselineTransformer module.
    Creates a model, runs a dummy forward pass, and prints parameter count.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test BaselineTransformer")
    parser.add_argument("--input_dim", type=int, default=4, help="Input dimension (e.g., Lorenz state)")
    parser.add_argument("--output_dim", type=int, default=4, help="Output dimension")
    parser.add_argument("--d_model", type=int, default=128, help="Model dimension")
    parser.add_argument("--n_heads", type=int, default=4, help="Number of attention heads")
    parser.add_argument("--n_layers", type=int, default=2, help="Number of transformer layers")
    parser.add_argument("--d_ff", type=int, default=256, help="Feed-forward dimension")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")
    parser.add_argument("--batch_size", type=int, default=4, help="Test batch size")
    parser.add_argument("--seq_len", type=int, default=20, help="Test sequence length")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    # Create model
    model = create_baseline_transformer(
        input_dim=args.input_dim,
        output_dim=args.output_dim,
        d_model=args.d_model,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
        d_ff=args.d_ff,
        dropout=args.dropout
    )
    
    total_params = count_parameters(model)
    logger.info(f"Total trainable parameters: {total_params}")
    
    # Dummy forward pass
    device = torch.device("cpu") # Default to CPU for this test
    model.to(device)
    
    dummy_input = torch.randn(args.batch_size, args.seq_len, args.input_dim).to(device)
    
    try:
        output = model(dummy_input)
        logger.info(f"Forward pass successful. Output shape: {output.shape}")
        assert output.shape == (args.batch_size, args.seq_len, args.output_dim), \
            f"Output shape mismatch: {output.shape} != expected {(args.batch_size, args.seq_len, args.output_dim)}"
        logger.info("Model structure and forward pass verified successfully.")
    except Exception as e:
        logger.error(f"Forward pass failed: {e}")
        raise

if __name__ == "__main__":
    main()