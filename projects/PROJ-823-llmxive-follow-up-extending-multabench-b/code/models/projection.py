"""
Projection modules for tabular-conditioned embedding modulation.

Implements:
- MLPProjection: Multi-layer perceptron based projection
- AttentionProjection: Single-head attention based projection
- GatedProjection: Gated mechanism for conditioning
"""
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple
import numpy as np
from models.base import ProjectionModel
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

class MLPProjection(ProjectionModel):
    """
    MLP-based projection module.

    Takes frozen embeddings and tabular features, concatenates them,
    and passes through an MLP to produce projected embeddings.
    """

    def __init__(
        self,
        embedding_dim: int,
        tabular_dim: int,
        output_dim: int,
        hidden_dims: Optional[List[int]] = None,
        dropout: float = 0.1,
        activation: str = "relu"
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.tabular_dim = tabular_dim
        self.output_dim = output_dim

        if hidden_dims is None:
            hidden_dims = [256, 128]

        input_dim = embedding_dim + tabular_dim

        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU() if activation == "relu" else nn.GELU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))
        self.network = nn.Sequential(*layers)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with Xavier initialization."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        return self.project(embeddings, tabular_features)

    def project(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings conditioned on tabular features.

        Args:
            embeddings: Frozen embeddings (B, D_emb)
            tabular_features: Tabular features (B, D_tab)

        Returns:
            Projected embeddings (B, D_out)
        """
        combined = torch.cat([embeddings, tabular_features], dim=-1)
        return self.network(combined)

    def get_conditioning_dim(self) -> int:
        return self.tabular_dim

    def get_output_dim(self) -> int:
        return self.output_dim

    def save(self, path: str) -> None:
        torch.save({
            'state_dict': self.state_dict(),
            'config': {
                'embedding_dim': self.embedding_dim,
                'tabular_dim': self.tabular_dim,
                'output_dim': self.output_dim,
                'hidden_dims': list(self.network[0].in_features) if hasattr(self.network[0], 'in_features') else []
            }
        }, path)
        log_info(logger, f"Model saved to {path}")

    def load(self, path: str) -> None:
        checkpoint = torch.load(path, map_location='cpu')
        self.load_state_dict(checkpoint['state_dict'])
        log_info(logger, f"Model loaded from {path}")

class AttentionProjection(ProjectionModel):
    """
    Attention-based projection module.

    Uses tabular features as queries to attend to frozen embeddings.
    """

    def __init__(
        self,
        embedding_dim: int,
        tabular_dim: int,
        output_dim: int,
        num_heads: int = 1,
        dropout: float = 0.1
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.tabular_dim = tabular_dim
        self.output_dim = output_dim
        self.num_heads = num_heads

        # Project tabular features to query dimension
        self.query_proj = nn.Linear(tabular_dim, embedding_dim)

        # Multi-head attention
        self.attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )

        # Output projection
        self.output_proj = nn.Linear(embedding_dim, output_dim)
        self.norm = nn.LayerNorm(embedding_dim)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        return self.project(embeddings, tabular_features)

    def project(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings using attention with tabular features as queries.

        Args:
            embeddings: Frozen embeddings (B, D_emb) - treated as key/value
            tabular_features: Tabular features (B, D_tab) - treated as query

        Returns:
            Projected embeddings (B, D_out)
        """
        # Ensure embeddings are (B, 1, D_emb) for attention
        # We treat the single embedding as a sequence of length 1
        # Actually, for this use case, we want to condition the embedding
        # using the tabular feature. Let's do cross-attention where
        # query = tabular, key/value = embedding.

        # Reshape for attention: (B, 1, D)
        q = self.query_proj(tabular_features).unsqueeze(1)  # (B, 1, D_emb)
        k = embeddings.unsqueeze(1)  # (B, 1, D_emb)
        v = embeddings.unsqueeze(1)  # (B, 1, D_emb)

        attn_out, _ = self.attention(q, k, v)
        attn_out = attn_out.squeeze(1)  # (B, D_emb)

        out = self.norm(attn_out)
        out = self.output_proj(out)
        return out

    def get_conditioning_dim(self) -> int:
        return self.tabular_dim

    def get_output_dim(self) -> int:
        return self.output_dim

    def save(self, path: str) -> None:
        torch.save({
            'state_dict': self.state_dict(),
            'config': {
                'embedding_dim': self.embedding_dim,
                'tabular_dim': self.tabular_dim,
                'output_dim': self.output_dim,
                'num_heads': self.num_heads
            }
        }, path)
        log_info(logger, f"Model saved to {path}")

    def load(self, path: str) -> None:
        checkpoint = torch.load(path, map_location='cpu')
        self.load_state_dict(checkpoint['state_dict'])
        log_info(logger, f"Model loaded from {path}")

class GatedProjection(ProjectionModel):
    """
    Gated projection module.

    Uses a gating mechanism to modulate embeddings based on tabular features.
    """

    def __init__(
        self,
        embedding_dim: int,
        tabular_dim: int,
        output_dim: int,
        gate_hidden_dim: int = 64,
        dropout: float = 0.1
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.tabular_dim = tabular_dim
        self.output_dim = output_dim

        # Gate network
        self.gate_net = nn.Sequential(
            nn.Linear(tabular_dim, gate_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(gate_hidden_dim, embedding_dim),
            nn.Sigmoid()
        )

        # Value network
        self.value_net = nn.Sequential(
            nn.Linear(tabular_dim, gate_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(gate_hidden_dim, embedding_dim)
        )

        # Output projection
        self.output_proj = nn.Linear(embedding_dim, output_dim)
        self.norm = nn.LayerNorm(embedding_dim)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        return self.project(embeddings, tabular_features)

    def project(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings using gated modulation.

        Args:
            embeddings: Frozen embeddings (B, D_emb)
            tabular_features: Tabular features (B, D_tab)

        Returns:
            Projected embeddings (B, D_out)
        """
        gate = self.gate_net(tabular_features)  # (B, D_emb)
        value = self.value_net(tabular_features)  # (B, D_emb)

        # Modulate: (1 - gate) * embedding + gate * value
        modulated = (1 - gate) * embeddings + gate * value
        modulated = self.norm(modulated)

        out = self.output_proj(modulated)
        return out

    def get_conditioning_dim(self) -> int:
        return self.tabular_dim

    def get_output_dim(self) -> int:
        return self.output_dim

    def save(self, path: str) -> None:
        torch.save({
            'state_dict': self.state_dict(),
            'config': {
                'embedding_dim': self.embedding_dim,
                'tabular_dim': self.tabular_dim,
                'output_dim': self.output_dim
            }
        }, path)
        log_info(logger, f"Model saved to {path}")

    def load(self, path: str) -> None:
        checkpoint = torch.load(path, map_location='cpu')
        self.load_state_dict(checkpoint['state_dict'])
        log_info(logger, f"Model loaded from {path}")

def create_projection_model(
    model_type: str,
    embedding_dim: int,
    tabular_dim: int,
    output_dim: int,
    **kwargs
) -> ProjectionModel:
    """
    Factory function to create a projection model.

    Args:
        model_type: One of 'mlp', 'attention', 'gated'
        embedding_dim: Dimension of frozen embeddings
        tabular_dim: Dimension of tabular features
        output_dim: Desired output dimension
        **kwargs: Additional model-specific arguments

    Returns:
        ProjectionModel instance
    """
    model_type = model_type.lower()

    if model_type == 'mlp':
        return MLPProjection(embedding_dim, tabular_dim, output_dim, **kwargs)
    elif model_type == 'attention':
        return AttentionProjection(embedding_dim, tabular_dim, output_dim, **kwargs)
    elif model_type == 'gated':
        return GatedProjection(embedding_dim, tabular_dim, output_dim, **kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}. Choose from 'mlp', 'attention', 'gated'")
