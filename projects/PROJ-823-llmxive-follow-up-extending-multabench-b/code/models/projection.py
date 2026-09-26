"""
Projection models for tabular-conditioned embedding modulation.

Implements various architectures for projecting frozen embeddings using
tabular metadata as conditioning signals.
"""
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
from models.base import ProjectionModel
from utils.logging import get_logger, log_info, log_error


logger = get_logger(__name__)


class MLPProjection(ProjectionModel):
    """
    Multi-Layer Perceptron (MLP) based projection model.

    Uses a series of linear layers with non-linear activations to project
    embeddings. Can optionally accept tabular features as an additional input.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dims: Optional[List[int]] = None,
        dropout: float = 0.1,
        activation: str = "relu",
        use_conditioning: bool = False,
        condition_dim: Optional[int] = None,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.use_conditioning = use_conditioning

        if hidden_dims is None:
            hidden_dims = [input_dim // 2, input_dim // 4]

        # Determine effective input dimension based on conditioning
        effective_input_dim = input_dim
        if use_conditioning:
            if condition_dim is None:
                raise ValueError("condition_dim must be provided when use_conditioning is True")
            effective_input_dim = input_dim + condition_dim

        layers = []
        prev_dim = effective_input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            if activation == "relu":
                layers.append(nn.ReLU())
            elif activation == "gelu":
                layers.append(nn.GELU())
            elif activation == "tanh":
                layers.append(nn.Tanh())
            else:
                raise ValueError(f"Unsupported activation: {activation}")
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, embeddings: torch.Tensor, conditions: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass.

        Args:
            embeddings: Tensor of shape (batch_size, input_dim).
            conditions: Optional tensor of shape (batch_size, condition_dim).

        Returns:
            Projected embeddings of shape (batch_size, output_dim).
        """
        if self.use_conditioning:
            if conditions is None:
                raise ValueError("Conditions are required when use_conditioning is True")
            x = torch.cat([embeddings, conditions], dim=1)
        else:
            x = embeddings

        return self.network(x)

    def project(self, embeddings: torch.Tensor, conditions: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Alias for forward."""
        return self.forward(embeddings, conditions)


class AttentionProjection(ProjectionModel):
    """
    Attention-based projection model.

    Uses self-attention or cross-attention to modulate embeddings based on
    conditioning information.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        num_heads: int = 4,
        head_dim: Optional[int] = None,
        dropout: float = 0.1,
        use_conditioning: bool = False,
        condition_dim: Optional[int] = None,
        num_layers: int = 1,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.use_conditioning = use_conditioning

        if head_dim is None:
            head_dim = input_dim // num_heads

        self.num_heads = num_heads
        self.head_dim = head_dim

        # Input projection
        self.input_proj = nn.Linear(input_dim, input_dim)

        if use_conditioning:
            if condition_dim is None:
                raise ValueError("condition_dim must be provided when use_conditioning is True")
            self.condition_proj = nn.Linear(condition_dim, input_dim)
            # Cross-attention layer
            self.cross_attn = nn.MultiheadAttention(
                embed_dim=input_dim,
                num_heads=num_heads,
                dropout=dropout,
                batch_first=True,
            )
            self.norm1 = nn.LayerNorm(input_dim)
            self.norm2 = nn.LayerNorm(input_dim)
        else:
            # Self-attention layer
            self.self_attn = nn.MultiheadAttention(
                embed_dim=input_dim,
                num_heads=num_heads,
                dropout=dropout,
                batch_first=True,
            )
            self.norm = nn.LayerNorm(input_dim)

        # FFN
        self.ffn = nn.Sequential(
            nn.Linear(input_dim, input_dim * 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(input_dim * 4, input_dim),
        )

        # Output projection
        self.output_proj = nn.Linear(input_dim, output_dim)

    def forward(
        self, embeddings: torch.Tensor, conditions: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            embeddings: Tensor of shape (batch_size, input_dim).
            conditions: Optional tensor of shape (batch_size, condition_dim).

        Returns:
            Projected embeddings of shape (batch_size, output_dim).
        """
        # Reshape for attention: (batch, seq_len=1, dim)
        x = self.input_proj(embeddings).unsqueeze(1)  # (B, 1, D)

        if self.use_conditioning:
            if conditions is None:
                raise ValueError("Conditions are required when use_conditioning is True")
            # Project conditions to same dimension
            c = self.condition_proj(conditions).unsqueeze(1)  # (B, 1, D)
            # Cross-attention: query is embeddings, key/value are conditions
            attn_out, _ = self.cross_attn(x, c, c)
            x = self.norm1(x + attn_out)

            # FFN
            ffn_out = self.ffn(x)
            x = self.norm2(x + ffn_out)
        else:
            # Self-attention
            attn_out, _ = self.self_attn(x, x, x)
            x = self.norm(x + attn_out)

            # FFN
            ffn_out = self.ffn(x)
            x = x + ffn_out

        # Output projection
        x = x.squeeze(1)  # (B, D)
        return self.output_proj(x)

    def project(self, embeddings: torch.Tensor, conditions: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Alias for forward."""
        return self.forward(embeddings, conditions)


class GatedProjection(ProjectionModel):
    """
    Gated projection model.

    Uses gating mechanisms to dynamically weight the contribution of
    conditioning information to the embedding projection.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dim: Optional[int] = None,
        dropout: float = 0.1,
        use_conditioning: bool = False,
        condition_dim: Optional[int] = None,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.use_conditioning = use_conditioning

        if hidden_dim is None:
            hidden_dim = input_dim

        self.hidden_dim = hidden_dim

        # Main projection path
        self.main_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

        if use_conditioning:
            if condition_dim is None:
                raise ValueError("condition_dim must be provided when use_conditioning is True")

            # Gating network
            self.gate_net = nn.Sequential(
                nn.Linear(condition_dim, hidden_dim),
                nn.Sigmoid(),
            )

            # Conditioning projection
            self.cond_proj = nn.Sequential(
                nn.Linear(condition_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, output_dim),
            )

    def forward(self, embeddings: torch.Tensor, conditions: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass.

        Args:
            embeddings: Tensor of shape (batch_size, input_dim).
            conditions: Optional tensor of shape (batch_size, condition_dim).

        Returns:
            Projected embeddings of shape (batch_size, output_dim).
        """
        # Main path
        out = self.main_proj(embeddings)

        if self.use_conditioning:
            if conditions is None:
                raise ValueError("Conditions are required when use_conditioning is True")

            # Compute gate
            gate = self.gate_net(conditions)

            # Conditioning path
            cond_out = self.cond_proj(conditions)

            # Gated combination
            out = out * (1 - gate) + cond_out * gate

        return out

    def project(self, embeddings: torch.Tensor, conditions: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Alias for forward."""
        return self.forward(embeddings, conditions)


def create_projection_model(
    model_type: str,
    input_dim: int,
    output_dim: int,
    **kwargs,
) -> ProjectionModel:
    """
    Factory function to create projection models.

    Args:
        model_type: Type of model ("mlp", "attention", "gated").
        input_dim: Dimension of input embeddings.
        output_dim: Dimension of output projections.
        **kwargs: Additional model-specific arguments.

    Returns:
        An instance of the requested ProjectionModel.
    """
    model_type = model_type.lower()

    if model_type == "mlp":
        return MLPProjection(input_dim=input_dim, output_dim=output_dim, **kwargs)
    elif model_type == "attention":
        return AttentionProjection(input_dim=input_dim, output_dim=output_dim, **kwargs)
    elif model_type == "gated":
        return GatedProjection(input_dim=input_dim, output_dim=output_dim, **kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}. Choose from 'mlp', 'attention', 'gated'.")
