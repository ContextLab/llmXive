import math
from typing import Optional, Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F

from utils.config import get_embed_dim, get_num_heads, get_vocab_size, get_max_seq_length, ConfigError


class CausalSelfAttention(nn.Module):
    """
    Standard causal self-attention block.
    Used in both AR and Diffusion models for consistency.
    """
    def __init__(self, embed_dim: int, num_heads: int):
        super().__init__()
        assert embed_dim % num_heads == 0, "Embed dim must be divisible by num_heads"
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=False)
        self.proj = nn.Linear(embed_dim, embed_dim, bias=False)

        self.scale = self.head_dim ** -0.5

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        B, T, C = x.size()

        # Q, K, V
        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        # Split heads
        q = q.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

        # Attention
        attn = (q @ k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        x = attn @ v

        # Reshape and project
        x = x.transpose(1, 2).contiguous().view(B, T, C)
        x = self.proj(x)
        return x


class BidirectionalSelfAttention(nn.Module):
    """
    Bidirectional (full) self-attention for diffusion model.
    Unlike CausalSelfAttention, it allows full context visibility.
    """
    def __init__(self, embed_dim: int, num_heads: int):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=False)
        self.proj = nn.Linear(embed_dim, embed_dim, bias=False)

        self.scale = self.head_dim ** -0.5

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        B, T, C = x.size()

        # Q, K, V
        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        # Split heads
        q = q.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

        # Attention
        attn = (q @ k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        x = attn @ v

        # Reshape and project
        x = x.transpose(1, 2).contiguous().view(B, T, C)
        x = self.proj(x)
        return x


class MLPBlock(nn.Module):
    """
    Multi-Layer Perceptron block with GELU activation.
    """
    def __init__(self, embed_dim: int, hidden_dim: Optional[int] = None):
        super().__init__()
        if hidden_dim is None:
            hidden_dim = embed_dim * 4
        self.fc1 = nn.Linear(embed_dim, hidden_dim, bias=False)
        self.fc2 = nn.Linear(hidden_dim, embed_dim, bias=False)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.act(x)
        x = self.fc2(x)
        return x


class TransformerBlock(nn.Module):
    """
    Standard Transformer block with residual connections and layer norm.
    Supports both causal and bidirectional attention.
    """
    def __init__(self, embed_dim: int, num_heads: int, bidirectional: bool = False):
        super().__init__()
        self.ln1 = nn.LayerNorm(embed_dim)
        self.attn = BidirectionalSelfAttention(embed_dim, num_heads) if bidirectional else CausalSelfAttention(embed_dim, num_heads)
        self.ln2 = nn.LayerNorm(embed_dim)
        self.mlp = MLPBlock(embed_dim)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = x + self.attn(self.ln1(x), mask=mask)
        x = x + self.mlp(self.ln2(x))
        return x


class DiffusionModel(nn.Module):
    """
    Bidirectional MDM (Masked Diffusion Model) for text generation.
    Uses bidirectional attention to model the full context.
    """
    def __init__(self, vocab_size: int, embed_dim: int, num_heads: int, num_layers: int, max_seq_length: int):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.num_layers = num_layers

        self.tok_emb = nn.Embedding(vocab_size, embed_dim)
        self.pos_emb = nn.Parameter(torch.zeros(1, max_seq_length, embed_dim))
        self.drop = nn.Dropout(0.1)

        # Bidirectional transformer blocks for diffusion
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, bidirectional=True)
            for _ in range(num_layers)
        ])

        self.ln_f = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, vocab_size, bias=False)

        # Tie weights
        self.head.weight = self.tok_emb.weight

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.zeros_(module.bias)
            torch.nn.init.ones_(module.weight)

    def forward(self, input_ids: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        B, T = input_ids.size()
        assert T <= self.pos_emb.size(1), f"Sequence length {T} exceeds max {self.pos_emb.size(1)}"

        x = self.tok_emb(input_ids)
        x = x + self.pos_emb[:, :T, :]
        x = self.drop(x)

        for block in self.blocks:
            x = block(x, mask=mask)

        x = self.ln_f(x)
        logits = self.head(x)
        return logits


def create_diffusion_model() -> DiffusionModel:
    """
    Factory function to create a DiffusionModel based on config.yaml parameters.
    """
    try:
        embed_dim = get_embed_dim()
        num_heads = get_num_heads()
        num_layers = get_num_layers()
        vocab_size = get_vocab_size()
        max_seq_length = get_max_seq_length()
    except ConfigError as e:
        raise RuntimeError(f"Failed to load model configuration: {e}")

    model = DiffusionModel(
        vocab_size=vocab_size,
        embed_dim=embed_dim,
        num_heads=num_heads,
        num_layers=num_layers,
        max_seq_length=max_seq_length
    )
    return model