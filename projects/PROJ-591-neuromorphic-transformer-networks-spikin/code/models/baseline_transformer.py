import torch
import torch.nn as nn
import math
from typing import Optional, Tuple

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

class BaselineTransformer(nn.Module):
    def __init__(self, vocab_size: int, d_model: int = 128, nhead: int = 4, num_layers: int = 2, dim_ff: int = 256, dropout: float = 0.1):
        super(BaselineTransformer, self).__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dim_feedforward=dim_ff, 
            dropout=dropout
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.decoder = nn.Linear(d_model, vocab_size)
        
        self.d_model = d_model

    def forward(self, src: torch.Tensor, src_mask: Optional[torch.Tensor] = None, src_key_padding_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        src = self.embedding(src) * math.sqrt(self.d_model)
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src, mask=src_mask, src_key_padding_mask=src_key_padding_mask)
        output = self.decoder(output)
        return output

def create_baseline_model(vocab_size: int = 10000, d_model: int = 128, nhead: int = 4, num_layers: int = 2, dim_ff: int = 256) -> BaselineTransformer:
    """
    Create a baseline Transformer model.
    
    Args:
        vocab_size: Size of vocabulary
        d_model: Dimension of model
        nhead: Number of attention heads
        num_layers: Number of encoder layers
        dim_ff: Dimension of feedforward network
        
    Returns:
        BaselineTransformer model
    """
    return BaselineTransformer(vocab_size=vocab_size, d_model=d_model, nhead=nhead, num_layers=num_layers, dim_ff=dim_ff)
