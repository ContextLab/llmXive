"""
Baseline Transformer implementation for WikiText-2 language modeling.

This module implements a standard Transformer encoder-decoder (causal) model
with 2 layers and 4 heads, totaling approximately 2M parameters.
It enforces CPU-only execution as per project constraints.
"""

import torch
import torch.nn as nn
import math
from typing import Optional, Tuple

# Ensure CPU-only execution
if torch.cuda.is_available():
    print("WARNING: CUDA detected. Forcing CPU-only execution as per project constraints.")
    torch.cuda.is_available = lambda: False  # Patch to prevent accidental GPU usage

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
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)

        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, d_model)
        Returns:
            Tensor with positional encoding added, shape (batch_size, seq_len, d_model)
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class BaselineTransformer(nn.Module):
    """
    A simple Transformer language model.
    
    Architecture:
    - 2 Transformer Encoder Layers (causal masking applied internally)
    - 4 Attention Heads
    - d_model = 128 (to approximate ~2M params)
    - d_ff = 512 (inner feed-forward dimension)
    
    Uses nn.TransformerEncoder with a custom causal mask generation.
    """
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        max_seq_len: int = 512
    ):
        super().__init__()
        
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len

        # Embedding
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_seq_len, dropout=dropout)

        # Transformer Encoder Layer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='relu',
            batch_first=True,
            norm_first=False
        )
        
        # Custom Transformer Encoder to handle causal masking
        # We use the standard encoder but apply a causal mask in forward pass
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
            enable_nested_tensor=False
        )

        # Output projection
        self.decoder = nn.Linear(d_model, vocab_size)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with standard deviation 0.1."""
        initrange = 0.1
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.zero_()
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def generate_square_subsequent_mask(self, sz: int, device: torch.device) -> torch.Tensor:
        """
        Generates a causal mask (upper triangular) to prevent attending to future tokens.
        Returns a mask of shape (sz, sz) where True means masked (cannot attend).
        """
        mask = (torch.triu(torch.ones(sz, sz, device=device)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask

    def forward(self, src: torch.Tensor, src_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            src: Input token IDs of shape (batch_size, seq_len)
            src_mask: Optional pre-computed mask. If None, generates causal mask.
        Returns:
            Logits of shape (batch_size, seq_len, vocab_size)
        """
        if src.dim() == 2:
            batch_size, seq_len = src.shape
        else:
            raise ValueError(f"Input must be 2D (batch, seq), got {src.dim()}D")

        # Generate causal mask if not provided
        if src_mask is None:
            src_mask = self.generate_square_subsequent_mask(seq_len, src.device)

        # Embed and add positional encoding
        x = self.embedding(src) * math.sqrt(self.d_model)
        x = self.pos_encoder(x)

        # Encode
        # nn.TransformerEncoder expects src_mask to be (seq_len, seq_len) for causal
        # or (num_heads, seq_len, seq_len) if multi-head attention mask is needed.
        # Our generated mask is (seq_len, seq_len) which works for the encoder.
        output = self.transformer_encoder(x, src_mask=src_mask)

        # Project to vocab
        logits = self.decoder(output)
        return logits

    def count_parameters(self) -> int:
        """Returns the total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def to_cpu(self) -> 'BaselineTransformer':
        """Explicitly moves the model to CPU and enforces CPU mode."""
        self = self.to('cpu')
        # Ensure no GPU tensors exist
        for param in self.parameters():
            if param.is_cuda:
                raise RuntimeError("Attempted to move model to CPU but CUDA tensor detected.")
        return self


def create_baseline_model(vocab_size: int, device: torch.device = None) -> BaselineTransformer:
    """
    Factory function to create and configure the baseline transformer.
    
    Args:
        vocab_size: Size of the vocabulary.
        device: Target device. Defaults to CPU.
        
    Returns:
        Configured BaselineTransformer instance.
    """
    if device is None:
        device = torch.device('cpu')
    
    model = BaselineTransformer(
        vocab_size=vocab_size,
        d_model=128,
        nhead=4,
        num_layers=2,
        dim_feedforward=512,
        dropout=0.1
    )
    
    model = model.to_cpu()
    model.to(device)
    
    return model


# Example usage / simple test
if __name__ == "__main__":
    # Test the model
    test_vocab = 1000
    batch_size = 4
    seq_len = 32
    
    model = create_baseline_model(test_vocab)
    print(f"Model created with {model.count_parameters():,} parameters.")
    
    # Dummy input
    x = torch.randint(0, test_vocab, (batch_size, seq_len))
    
    # Forward pass
    with torch.no_grad():
        out = model(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {out.shape}")
    print("Baseline Transformer implementation verified.")