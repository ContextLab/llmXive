"""
Lightweight Transformer encoder for translation-only stability prediction.
Constrained to <10M parameters as per US2 requirements.
"""
import torch
import torch.nn as nn
import math
from typing import Optional

class TranslationTransformer(nn.Module):
    """
    A 4-layer Transformer encoder that processes translation trajectories.
    Designed for CPU-only execution and <10M parameters.
    """
    def __init__(self, 
                 input_size: int = 3,  # x, y, z translation
                 d_model: int = 64,
                 nhead: int = 4,
                 num_layers: int = 4,
                 dim_feedforward: int = 128,
                 dropout: float = 0.1,
                 max_seq_len: int = 100):
        super().__init__()
        
        self.input_size = input_size
        self.d_model = d_model
        
        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)
        
        # Positional encoding
        self.pos_encoder = self._generate_positional_encoding(max_seq_len, d_model)
        
        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output head (binary classification)
        self.output_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )
        
        self._init_weights()

    def _generate_positional_encoding(self, max_len: int, d_model: int) -> torch.Tensor:
        """Generate sinusoidal positional encodings."""
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model % 2 == 0:
            pe[:, 1::2] = torch.cos(position * div_term)
        else:
            pe[:, 1::2] = torch.cos(position * div_term[:-1])
        
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        return pe

    def _init_weights(self):
        """Initialize weights for better convergence."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: Input tensor of shape [batch_size, seq_len, input_size]
        Returns:
            Logits of shape [batch_size, 1]
        """
        batch_size, seq_len, _ = x.size()
        
        # Project input to model dimension
        x = self.input_projection(x)  # [batch, seq, d_model]
        
        # Add positional encoding
        # Truncate or pad positional encoding to match sequence length
        if seq_len <= self.pos_encoder.size(1):
            pos_enc = self.pos_encoder[:, :seq_len, :]
        else:
            # Generate additional positional encoding if needed
            pos_enc = self._generate_positional_encoding(seq_len, self.d_model)
        
        x = x + pos_enc.to(x.device)
        
        # Pass through transformer encoder
        x = self.transformer_encoder(x)  # [batch, seq, d_model]
        
        # Pool over sequence dimension (mean pooling)
        x = x.mean(dim=1)  # [batch, d_model]
        
        # Output head
        logits = self.output_head(x)  # [batch, 1]
        
        return logits

def count_parameters(model: nn.Module) -> int:
    """Count total number of parameters in a model."""
    return sum(p.numel() for p in model.parameters())
