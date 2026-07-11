"""
Projection module for MulTaBench extension.

Implements a lightweight projection layer (MLP or single-head attention)
that accepts tabular features as queries to modulate frozen embeddings.
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
    Multi-Layer Perceptron projection module.
    
    Takes frozen embeddings as key/value and tabular features as query
    to produce a conditioned representation.
    """
    def __init__(
        self,
        embedding_dim: int,
        tabular_dim: int,
        hidden_dim: int = 256,
        output_dim: Optional[int] = None,
        dropout: float = 0.1,
        num_layers: int = 2
    ):
        """
        Initialize the MLP projection.
        
        Args:
            embedding_dim: Dimension of the frozen embeddings.
            tabular_dim: Dimension of the tabular feature vector.
            hidden_dim: Hidden layer dimension for the MLP.
            output_dim: Output dimension (defaults to embedding_dim).
            dropout: Dropout probability.
            num_layers: Number of hidden layers in the MLP.
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.tabular_dim = tabular_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim or embedding_dim
        self.num_layers = num_layers

        # Query projection: maps tabular features to embedding space
        self.query_proj = nn.Sequential(
            nn.Linear(tabular_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # Key/Value projection: maps embeddings to attention space
        self.key_proj = nn.Linear(embedding_dim, hidden_dim)
        self.value_proj = nn.Linear(embedding_dim, hidden_dim)

        # Output projection
        output_layers = []
        current_dim = hidden_dim
        for _ in range(num_layers - 1):
            output_layers.append(nn.Linear(current_dim, hidden_dim))
            output_layers.append(nn.ReLU())
            output_layers.append(nn.Dropout(dropout))
            current_dim = hidden_dim
        output_layers.append(nn.Linear(hidden_dim, self.output_dim))
        
        self.output_proj = nn.Sequential(*output_layers)

        self._init_weights()

    def _init_weights(self):
        """Initialize weights using Xavier uniform."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        embeddings: torch.Tensor,
        tabular_features: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass of the MLP projection.
        
        Args:
            embeddings: Frozen embeddings of shape (batch_size, embedding_dim).
            tabular_features: Tabular features of shape (batch_size, tabular_dim).
            mask: Optional attention mask.
        
        Returns:
            Conditioned embeddings of shape (batch_size, output_dim).
        """
        # Project tabular features to query
        query = self.query_proj(tabular_features)  # (batch, hidden_dim)
        
        # Project embeddings to key/value
        key = self.key_proj(embeddings)  # (batch, hidden_dim)
        value = self.value_proj(embeddings)  # (batch, hidden_dim)
        
        # Compute attention weights (single-head, simplified)
        # Using dot product attention: scores = query @ key.T
        # Since we want to modulate the embedding, we compute a weighted sum
        # Here we use a simplified approach: query acts as a selector/modulator
        
        # Compute attention scores
        # For a single query per sample, we compute similarity with all embeddings
        # But since embeddings and tabular features are 1:1, we do element-wise modulation
        
        # Modulation approach: 
        # 1. Compute attention score between query and key (element-wise or dot product)
        # 2. Use score to weight value
        
        # Simple element-wise modulation for 1:1 mapping:
        # attention_weights = torch.sigmoid(query * key)  # (batch, hidden_dim)
        # But let's do a more robust approach: dot product then softmax over features
        
        # Reshape for attention: (batch, 1, hidden) @ (batch, hidden, 1) -> (batch, 1, 1)
        query_expanded = query.unsqueeze(1)  # (batch, 1, hidden)
        key_expanded = key.unsqueeze(2)      # (batch, hidden, 1)
        
        # Dot product attention score
        attention_scores = torch.bmm(query_expanded, key_expanded).squeeze(-1)  # (batch, 1)
        
        # Normalize attention scores (softmax over the single value is just sigmoid or identity)
        # Since we have one query per embedding, we use sigmoid to get a weight in [0, 1]
        attention_weights = torch.sigmoid(attention_scores)  # (batch, 1)
        
        # Apply attention to value
        value_expanded = value.unsqueeze(1)  # (batch, 1, hidden)
        attended_value = attention_weights.unsqueeze(-1) * value_expanded  # (batch, 1, hidden)
        
        # Squeeze and project to output
        attended_value = attended_value.squeeze(1)  # (batch, hidden)
        output = self.output_proj(attended_value)  # (batch, output_dim)
        
        return output


class AttentionProjection(ProjectionModel):
    """
    Single-head attention projection module.
    
    Uses tabular features as query to attend over frozen embeddings.
    """
    def __init__(
        self,
        embedding_dim: int,
        tabular_dim: int,
        hidden_dim: int = 256,
        output_dim: Optional[int] = None,
        dropout: float = 0.1,
        num_heads: int = 1
    ):
        """
        Initialize the attention projection.
        
        Args:
            embedding_dim: Dimension of the frozen embeddings.
            tabular_dim: Dimension of the tabular feature vector.
            hidden_dim: Hidden dimension for projections.
            output_dim: Output dimension (defaults to embedding_dim).
            dropout: Dropout probability.
            num_heads: Number of attention heads (set to 1 for single-head).
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.tabular_dim = tabular_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim or embedding_dim
        self.num_heads = num_heads

        if num_heads != 1:
            log_warning("AttentionProjection is designed for single-head attention. num_heads will be forced to 1.")
            self.num_heads = 1

        # Query projection from tabular features
        self.query_proj = nn.Linear(tabular_dim, hidden_dim)
        
        # Key and Value projections from embeddings
        self.key_proj = nn.Linear(embedding_dim, hidden_dim)
        self.value_proj = nn.Linear(embedding_dim, hidden_dim)

        # Output projection
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, self.output_dim)
        )

        self.dropout = nn.Dropout(dropout)
        self._init_weights()

    def _init_weights(self):
        """Initialize weights using Xavier uniform."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        embeddings: torch.Tensor,
        tabular_features: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass of the attention projection.
        
        Args:
            embeddings: Frozen embeddings of shape (batch_size, embedding_dim).
            tabular_features: Tabular features of shape (batch_size, tabular_dim).
            mask: Optional attention mask (not used in 1:1 mapping).
        
        Returns:
            Conditioned embeddings of shape (batch_size, output_dim).
        """
        batch_size = embeddings.size(0)

        # Project tabular features to query
        query = self.query_proj(tabular_features)  # (batch, hidden_dim)
        
        # Project embeddings to key/value
        key = self.key_proj(embeddings)  # (batch, hidden_dim)
        value = self.value_proj(embeddings)  # (batch, hidden_dim)
        
        # Reshape for attention computation
        # We treat each sample independently: query attends to its corresponding embedding
        # For a 1:1 mapping, we compute a single attention weight per sample
        
        # Expand dimensions for matrix multiplication
        query_exp = query.unsqueeze(1)  # (batch, 1, hidden)
        key_exp = key.unsqueeze(2)      # (batch, hidden, 1)
        
        # Compute attention score
        attention_scores = torch.bmm(query_exp, key_exp).squeeze(-1)  # (batch, 1)
        
        # Apply softmax (though with single element, it's just normalization)
        # Use sigmoid for bounded weights in [0, 1] for modulation
        attention_weights = torch.sigmoid(attention_scores)  # (batch, 1)
        
        # Apply attention to value
        value_exp = value.unsqueeze(1)  # (batch, 1, hidden)
        attended_value = attention_weights.unsqueeze(-1) * value_exp  # (batch, 1, hidden)
        
        # Squeeze and project to output
        attended_value = attended_value.squeeze(1)  # (batch, hidden)
        output = self.output_proj(attended_value)  # (batch, output_dim)
        
        return output


def create_projection_model(
    model_type: str = "mlp",
    embedding_dim: int = 512,
    tabular_dim: int = 128,
    hidden_dim: int = 256,
    output_dim: Optional[int] = None,
    dropout: float = 0.1,
    num_layers: int = 2,
    num_heads: int = 1
) -> ProjectionModel:
    """
    Factory function to create a projection model.
    
    Args:
        model_type: Type of projection model ("mlp" or "attention").
        embedding_dim: Dimension of frozen embeddings.
        tabular_dim: Dimension of tabular features.
        hidden_dim: Hidden dimension for the model.
        output_dim: Output dimension (defaults to embedding_dim).
        dropout: Dropout probability.
        num_layers: Number of layers for MLP.
        num_heads: Number of attention heads (for attention model).
        
    Returns:
        An instance of ProjectionModel.
    """
    if model_type.lower() == "mlp":
        return MLPProjection(
            embedding_dim=embedding_dim,
            tabular_dim=tabular_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            dropout=dropout,
            num_layers=num_layers
        )
    elif model_type.lower() == "attention":
        return AttentionProjection(
            embedding_dim=embedding_dim,
            tabular_dim=tabular_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            dropout=dropout,
            num_heads=num_heads
        )
    else:
        raise ValueError(f"Unknown projection model type: {model_type}. Use 'mlp' or 'attention'.")