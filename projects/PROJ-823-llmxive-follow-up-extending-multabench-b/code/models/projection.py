"""
Projection modules for modulating frozen embeddings with tabular features.

Implementations:
- MLPProjection: Simple Multi-Layer Perceptron projection.
- AttentionProjection: Single-head attention mechanism using tabular features as query.
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
    MLP-based projection layer.
    Maps (embedding, tabular) -> projected_embedding.
    Architecture: Concat -> Linear -> ReLU -> Linear -> Output
    """

    def __init__(
        self,
        input_dim: int,
        tabular_dim: int,
        output_dim: int,
        hidden_dim: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(input_dim, output_dim, config)
        self.tabular_dim = tabular_dim
        self.hidden_dim = hidden_dim or (input_dim + tabular_dim) // 2

        self.concat_proj = nn.Sequential(
            nn.Linear(input_dim + tabular_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Dropout(p=0.1),
            nn.Linear(self.hidden_dim, output_dim),
        )

        log_info(logger, f"Initialized MLPProjection: in={input_dim}+{tabular_dim}, out={output_dim}, hidden={self.hidden_dim}")

    def project(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings conditioned on tabular features.
        Args:
            embeddings: [B, input_dim]
            tabular_features: [B, tabular_dim]
        Returns:
            [B, output_dim]
        """
        if embeddings.shape[0] != tabular_features.shape[0]:
            raise ValueError(f"Batch size mismatch: embeddings {embeddings.shape[0]} vs tabular {tabular_features.shape[0]}")
        
        combined = torch.cat([embeddings, tabular_features], dim=-1)
        return self.concat_proj(combined)


class AttentionProjection(ProjectionModel):
    """
    Attention-based projection.
    Uses tabular features as Query to attend to the Embedding (Key/Value).
    Assumes embeddings are a sequence of length 1 or treated as a single vector.
    """

    def __init__(
        self,
        input_dim: int,
        tabular_dim: int,
        output_dim: int,
        n_heads: int = 1,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(input_dim, output_dim, config)
        self.tabular_dim = tabular_dim
        
        # Project tabular features to query space
        self.query_proj = nn.Linear(tabular_dim, input_dim)
        
        # Multi-head attention (treating embedding as a single token)
        self.attention = nn.MultiheadAttention(
            embed_dim=input_dim,
            num_heads=n_heads,
            dropout=0.1,
            batch_first=True
        )
        
        # Output projection
        self.output_proj = nn.Linear(input_dim, output_dim)

        log_info(logger, f"Initialized AttentionProjection: input={input_dim}, tabular={tabular_dim}, output={output_dim}, heads={n_heads}")

    def project(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings conditioned on tabular features.
        Args:
            embeddings: [B, input_dim] -> reshape to [B, 1, input_dim]
            tabular_features: [B, tabular_dim] -> reshape to [B, 1, input_dim] for query
        Returns:
            [B, output_dim]
        """
        batch_size = embeddings.shape[0]
        
        # Reshape embeddings to [B, 1, D]
        k = embeddings.unsqueeze(1)  # [B, 1, D]
        v = k
        
        # Project tabular features to query space [B, 1, D]
        q = self.query_proj(tabular_features).unsqueeze(1)
        
        attn_out, _ = self.attention(q, k, v)
        # attn_out shape: [B, 1, D]
        
        out = self.output_proj(attn_out.squeeze(1)) # [B, output_dim]
        return out


def create_projection_model(
    model_type: str,
    input_dim: int,
    tabular_dim: int,
    output_dim: int,
    config: Optional[Dict[str, Any]] = None
) -> ProjectionModel:
    """
    Factory function to create a projection model.

    Args:
        model_type: 'mlp' or 'attention'
        input_dim: Dimension of the frozen embeddings
        tabular_dim: Dimension of the tabular features
        output_dim: Desired output dimension
        config: Optional config dict

    Returns:
        ProjectionModel instance
    """
    if model_type.lower() == "mlp":
        hidden = config.get("hidden_dim") if config else None
        return MLPProjection(input_dim, tabular_dim, output_dim, hidden_dim=hidden, config=config)
    elif model_type.lower() == "attention":
        n_heads = config.get("n_heads", 1) if config else 1
        return AttentionProjection(input_dim, tabular_dim, output_dim, n_heads=n_heads, config=config)
    else:
        raise ValueError(f"Unknown projection model type: {model_type}. Supported: 'mlp', 'attention'")
