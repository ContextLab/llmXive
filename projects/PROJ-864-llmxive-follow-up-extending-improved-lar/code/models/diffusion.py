"""
Diffusion Model Implementation.

Implements a Bidirectional Masked Diffusion Model (MDM) using Transformer blocks
for sequence generation via iterative denoising.
"""

import math
from typing import Optional, Tuple, List
import torch
import torch.nn as nn
import torch.nn.functional as F
from utils.config import get_embed_dim, get_num_heads, get_vocab_size, get_max_seq_length, ConfigError


class CausalSelfAttention(nn.Module):
    """
    Bidirectional Self-Attention block (no causal masking).
    Used in the Diffusion model for full context access.
    """
    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        if self.head_dim * num_heads != embed_dim:
            raise ValueError(f"embed_dim ({embed_dim}) must be divisible by num_heads ({num_heads})")

        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=True)
        self.proj = nn.Linear(embed_dim, embed_dim, bias=True)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        batch_size, seq_len, embed_dim = x.size()

        # Project to Q, K, V
        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        # Reshape for multi-head attention
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        # Compute attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)

        # Apply mask if provided (standard bidirectional, no causal mask)
        if attention_mask is not None:
            scores = scores + attention_mask

        # Softmax and dropout
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Apply attention to values
        attn_output = torch.matmul(attn_weights, v)

        # Reshape and project
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, embed_dim)
        output = self.proj(attn_output)

        return output


class MLPBlock(nn.Module):
    """
    Multi-Layer Perceptron block used in Transformer layers.
    """
    def __init__(self, embed_dim: int, hidden_dim: Optional[int] = None, dropout: float = 0.1):
        super().__init__()
        if hidden_dim is None:
            hidden_dim = embed_dim * 4
        self.fc1 = nn.Linear(embed_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.dropout(x)
        return x


class TransformerBlock(nn.Module):
    """
    A single Transformer block containing self-attention and MLP.
    """
    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        self.ln1 = nn.LayerNorm(embed_dim)
        self.attn = CausalSelfAttention(embed_dim, num_heads, dropout)
        self.ln2 = nn.LayerNorm(embed_dim)
        self.mlp = MLPBlock(embed_dim, dropout=dropout)

    def forward(self, x: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Pre-norm architecture
        residual = x
        x = self.ln1(x)
        x = self.attn(x, attention_mask)
        x = x + residual

        residual = x
        x = self.ln2(x)
        x = self.mlp(x)
        x = x + residual

        return x


class DiffusionModel(nn.Module):
    """
    Full Bidirectional Diffusion Model for masked sequence modeling.
    """
    def __init__(self, vocab_size: int, embed_dim: int, num_heads: int, num_layers: int, max_seq_length: int, dropout: float = 0.1):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.max_seq_length = max_seq_length

        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.pos_embedding = nn.Embedding(max_seq_length, embed_dim)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, embed_dim)) # Learnable mask token
        self.dropout = nn.Dropout(dropout)

        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, dropout) for _ in range(num_layers)
        ])

        self.ln_f = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size, bias=False)

        # Tie weights
        self.lm_head.weight = self.token_embedding.weight

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass for the diffusion model.
        Handles masked token inputs by replacing them with the mask embedding.
        """
        batch_size, seq_len = input_ids.size()

        if seq_len > self.max_seq_length:
            raise ValueError(f"Sequence length {seq_len} exceeds max_seq_length {self.max_seq_length}")

        # Create mask embedding for masked positions (assuming -100 or specific ID is mask)
        # For simplicity, we assume input_ids with a specific value (e.g., vocab_size) is the mask token
        # In a real diffusion setup, this might be more complex
        mask_token_id = self.vocab_size # Assuming out-of-vocab ID is mask
        is_masked = (input_ids == mask_token_id).float()

        # Embed tokens
        token_emb = self.token_embedding(input_ids)

        # Replace masked positions with mask embedding
        mask_expanded = is_masked.unsqueeze(-1).expand_as(token_emb)
        token_emb = token_emb * (1 - mask_expanded) + self.mask_token * mask_expanded

        # Position embeddings
        pos_emb = self.pos_embedding(torch.arange(seq_len, device=input_ids.device).unsqueeze(0))
        x = self.dropout(token_emb + pos_emb)

        # Apply transformer blocks
        for block in self.transformer_blocks:
            x = block(x, attention_mask)

        x = self.ln_f(x)
        logits = self.lm_head(x)

        return logits


def create_diffusion_model() -> DiffusionModel:
    """
    Factory function to create a DiffusionModel with project configuration.

    Returns:
        DiffusionModel instance configured with project hyperparameters.
    """
    vocab_size = get_vocab_size()
    embed_dim = get_embed_dim()
    num_heads = get_num_heads()
    max_seq_length = get_max_seq_length()

    # Num layers is fetched from config, defaulting if necessary
    try:
        from models.config import get_num_layers
        num_layers = get_num_layers()
    except (ImportError, ConfigError):
        num_layers = 12

    try:
        from models.config import get_dropout
        dropout = get_dropout()
    except (ImportError, ConfigError):
        dropout = 0.1

    return DiffusionModel(
        vocab_size=vocab_size,
        embed_dim=embed_dim,
        num_heads=num_heads,
        num_layers=num_layers,
        max_seq_length=max_seq_length,
        dropout=dropout
    )