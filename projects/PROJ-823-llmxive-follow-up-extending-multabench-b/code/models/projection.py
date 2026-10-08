"""
T024g: Fixed projection.py to add missing List import
"""
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
from models.base import ProjectionModel
from utils.logging import get_logger, log_info, log_error

class MLPProjection(ProjectionModel):
    """Multi-Layer Perceptron projection model."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dims: Optional[List[int]] = None,
        dropout: float = 0.1,
        activation: str = "relu"
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dims = hidden_dims or [256, 128]
        self.dropout = dropout
        self.activation = activation

        layers = []
        prev_dim = input_dim

        for hidden_dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            if activation == "relu":
                layers.append(nn.ReLU())
            elif activation == "gelu":
                layers.append(nn.GELU())
            layers.append(nn.Dropout(self.dropout))
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))
        self.model = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

class AttentionProjection(ProjectionModel):
    """Attention-based projection model."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        num_heads: int = 4,
        hidden_dim: int = 128
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.hidden_dim = hidden_dim

        self.query_proj = nn.Linear(input_dim, hidden_dim)
        self.key_proj = nn.Linear(input_dim, hidden_dim)
        self.value_proj = nn.Linear(input_dim, hidden_dim)
        self.output_proj = nn.Linear(hidden_dim, output_dim)
        self.attention_scale = hidden_dim ** 0.5

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, input_dim)
        # For simplicity, treat each sample as a single token
        q = self.query_proj(x)  # (batch, hidden)
        k = self.key_proj(x)    # (batch, hidden)
        v = self.value_proj(x)  # (batch, hidden)

        # Self-attention (single token, so just scale)
        attention_weights = torch.softmax((q * k) / self.attention_scale, dim=-1)
        attended = attention_weights * v

        return self.output_proj(attended)

class GatedProjection(ProjectionModel):
    """Gated projection model with residual connections."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dim: int = 256
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dim = hidden_dim

        self.main_path = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )

        self.gate_path = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Sigmoid(),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        main_out = self.main_path(x)
        gate_out = self.gate_path(x)
        return main_out * gate_out

def create_projection_model(
    model_type: str,
    input_dim: int,
    output_dim: int,
    **kwargs
) -> ProjectionModel:
    """Factory function to create projection models."""
    model_type = model_type.lower()

    if model_type == "mlp":
        return MLPProjection(input_dim, output_dim, **kwargs)
    elif model_type == "attention":
        return AttentionProjection(input_dim, output_dim, **kwargs)
    elif model_type == "gated":
        return GatedProjection(input_dim, output_dim, **kwargs)
    else:
        raise ValueError(f"Unknown projection model type: {model_type}")
