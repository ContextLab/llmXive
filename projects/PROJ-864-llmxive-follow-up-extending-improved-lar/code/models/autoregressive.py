"""
Autoregressive (Causal Language Model) implementation for the llmXive project.

This module defines a large-scale Causal LM (Transformer decoder-only)
designed to match the parameter counts and hyperparameters specified in
the project configuration (T007: EMBED_DIM=768, NUM_HEADS=12, PARAMS=100M+).

The model uses standard causal self-attention and is compatible with
CPU-optimized training loops via torch.compile.
"""
import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from utils.config import get_embed_dim, get_num_heads, get_vocab_size, get_max_seq_length, ConfigError
from utils.logging import get_logger
from models.config import get_model_config

logger = get_logger(__name__)


class CausalSelfAttention(nn.Module):
    """
    Causal Self-Attention layer with rotary-style masking implemented via
    standard causal mask for CPU efficiency.
    """
    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=False)

        self.dropout = dropout
        self.register_buffer("bias", torch.tril(torch.ones(get_max_seq_length(), get_max_seq_length()))
                                   .view(1, 1, get_max_seq_length(), get_max_seq_length()))

    def forward(self, x: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        B, T, C = x.size()  # batch, sequence, embed_dim

        # Calculate Q, K, V
        q = self.q_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

        # Causal mask: only attend to past
        # mask shape: (1, 1, T, T)
        mask = self.bias[:, :, :T, :T]

        # Attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) * (1.0 / math.sqrt(self.head_dim))

        # Apply causal mask
        scores = scores.masked_fill(mask == 0, float('-inf'))

        # Apply attention mask if provided (e.g., for padding)
        if attention_mask is not None:
            # attention_mask expected to be (B, T) or (B, 1, 1, T)
            if attention_mask.dim() == 2:
                attention_mask = attention_mask.view(B, 1, 1, T)
            scores = scores.masked_fill(attention_mask == 0, float('-inf'))

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = F.dropout(attn_weights, p=self.dropout, training=self.training)

        # Apply attention to values
        attn_output = torch.matmul(attn_weights, v)

        # Reshape back to (B, T, C)
        attn_output = attn_output.transpose(1, 2).contiguous().view(B, T, C)

        # Project output
        output = self.out_proj(attn_output)
        return output


class MLPBlock(nn.Module):
    """
    Feed-forward network block with GELU activation.
    """
    def __init__(self, embed_dim: int, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.c_fc = nn.Linear(embed_dim, hidden_dim, bias=False)
        self.c_proj = nn.Linear(hidden_dim, embed_dim, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.c_fc(x)
        x = F.gelu(x)
        x = self.c_proj(x)
        x = self.dropout(x)
        return x


class TransformerBlock(nn.Module):
    """
    A single Transformer block containing Causal Attention and MLP.
    """
    def __init__(self, embed_dim: int, num_heads: int, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.ln_1 = nn.LayerNorm(embed_dim)
        self.attn = CausalSelfAttention(embed_dim, num_heads, dropout)
        self.ln_2 = nn.LayerNorm(embed_dim)
        self.mlp = MLPBlock(embed_dim, hidden_dim, dropout)

    def forward(self, x: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Pre-normalization architecture
        x = x + self.attn(self.ln_1(x), attention_mask)
        x = x + self.mlp(self.ln_2(x))
        return x


class AutoregressiveModel(nn.Module):
    """
    Full Causal Language Model (Decoder-only Transformer).

    Architecture:
    - Embedding layer
    - N Transformer blocks
    - Output projection to vocab
    - No bias in Linear layers (as per modern LLM practices)
    """
    def __init__(self, config: Optional[dict] = None):
        super().__init__()

        if config is None:
            try:
                config = get_model_config("autoregressive")
            except ConfigError as e:
                logger.error(f"Failed to load model config: {e}")
                raise

        self.embed_dim = config.get("embed_dim", get_embed_dim())
        self.num_heads = config.get("num_heads", get_num_heads())
        self.vocab_size = config.get("vocab_size", get_vocab_size())
        self.max_seq_length = config.get("max_seq_length", get_max_seq_length())
        self.num_layers = config.get("num_layers", 12) # Default to ~100M params with 768 dim
        self.dropout = config.get("dropout", 0.1)

        # Calculate hidden dim for MLP (usually 4x embed_dim)
        self.hidden_dim = self.embed_dim * 4

        logger.info(f"Initializing AutoregressiveModel: "
                    f"embed_dim={self.embed_dim}, heads={self.num_heads}, "
                    f"layers={self.num_layers}, vocab={self.vocab_size}")

        # Embeddings
        self.tok_embeddings = nn.Embedding(self.vocab_size, self.embed_dim)
        self.pos_embeddings = nn.Embedding(self.max_seq_length, self.embed_dim)

        # Transformer blocks
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(self.embed_dim, self.num_heads, self.hidden_dim, self.dropout)
            for _ in range(self.num_layers)
        ])

        # Output projection
        self.output_projection = nn.Linear(self.embed_dim, self.vocab_size, bias=False)

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            nn.init.ones_(module.weight)
            nn.init.zeros_(module.bias)

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            input_ids: (B, T) tensor of token ids
            attention_mask: (B, T) tensor (1 for valid, 0 for padding)
        Returns:
            logits: (B, T, vocab_size)
        """
        B, T = input_ids.size()
        assert T <= self.max_seq_length, f"Sequence length {T} exceeds max {self.max_seq_length}"

        # Token embeddings
        x = self.tok_embeddings(input_ids)

        # Position embeddings
        pos_ids = torch.arange(T, device=input_ids.device).unsqueeze(0)
        x = x + self.pos_embeddings(pos_ids)

        # Apply transformer blocks
        for block in self.transformer_blocks:
            x = block(x, attention_mask)

        # Project to logits
        logits = self.output_projection(x)

        return logits

    def get_num_parameters(self) -> int:
        """Calculate total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def create_autoregressive_model() -> AutoregressiveModel:
    """
    Factory function to create the autoregressive model using project config.
    """
    return AutoregressiveModel()


# For compatibility with tests that might expect a class name
Model = AutoregressiveModel