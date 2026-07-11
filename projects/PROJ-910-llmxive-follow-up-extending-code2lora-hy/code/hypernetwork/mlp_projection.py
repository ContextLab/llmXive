"""
MLP Projection Layer for Code2LoRA Hypernetwork.

This module defines a lightweight Multi-Layer Perceptron (MLP) that maps
static AST feature vectors to the base model's embedding dimension.
It serves as the core projection mechanism in the hypernetwork architecture,
replacing the original neural encoder with a computationally efficient
static-feature-based approach.

Dependencies:
    - config.feature_vector_size: Input dimension (derived from AST features)
    - config.hidden_size / embedding_dim: Output dimension (base model config)
"""

import torch
import torch.nn as nn
from typing import Tuple, Optional

from utils.config import Config


class MLPProjection(nn.Module):
    """
    A small MLP (ReLU-based) that projects AST feature vectors to the
    base model's embedding dimension.

    Architecture:
        Input (feature_vector_size) -> Linear -> ReLU -> Linear -> Output (embedding_dim)

    This design ensures:
        1. Differentiable mapping from static code features to model parameters.
        2. Minimal computational overhead compared to neural encoders.
        3. Compatibility with LoRA adapter injection mechanisms.
    """

    def __init__(self, config: Config, base_model_config: Optional[dict] = None):
        """
        Initialize the MLP projection layer.

        Args:
            config: Project configuration object containing feature_vector_size.
            base_model_config: Optional dict containing 'hidden_size' or 'embedding_dim'
                               from the loaded base model config. If None, attempts to
                               infer from config or defaults to a standard size (e.g., 768).
        """
        super().__init__()

        # Determine input dimension from config
        self.input_dim = config.feature_vector_size
        if self.input_dim is None or self.input_dim <= 0:
            raise ValueError(
                f"Invalid feature_vector_size in config: {config.feature_vector_size}. "
                "Ensure T005 (config.py) has correctly loaded the feature vector size."
            )

        # Determine output dimension (embedding dimension)
        # Priority: base_model_config -> config.embedding_dim -> config.hidden_size -> default
        if base_model_config:
            self.output_dim = base_model_config.get('hidden_size') or base_model_config.get('embedding_dim')
        else:
            self.output_dim = getattr(config, 'embedding_dim', None) or getattr(config, 'hidden_size', 768)

        if not self.output_dim or self.output_dim <= 0:
            # Fallback if not explicitly set, though T005 should handle this
            self.output_dim = 768

        # Define the MLP layers
        # Layer 1: Input -> Hidden (ReLU)
        self.fc1 = nn.Linear(self.input_dim, self.input_dim * 2)
        self.relu = nn.ReLU()
        # Layer 2: Hidden -> Output
        self.fc2 = nn.Linear(self.input_dim * 2, self.output_dim)

        # Optional Layer 3 for deeper projection if input is very large (heuristic)
        if self.input_dim > 2048:
            self.fc3 = nn.Linear(self.input_dim * 2, self.input_dim * 2)
            self.fc4 = nn.Linear(self.input_dim * 2, self.output_dim)
            self.layers = nn.Sequential(
                self.fc1, self.relu, self.fc3, self.relu, self.fc4
            )
        else:
            self.layers = nn.Sequential(self.fc1, self.relu, self.fc2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the MLP.

        Args:
            x: Input tensor of shape (batch_size, feature_vector_size).

        Returns:
            Tensor of shape (batch_size, embedding_dim).
        """
        # Ensure input is float
        if x.dtype != torch.float32:
            x = x.float()

        # Validate input shape
        if x.dim() != 2:
            raise ValueError(f"Expected 2D input (batch, features), got shape: {x.shape}")

        if x.shape[1] != self.input_dim:
            raise ValueError(
                f"Input feature dimension {x.shape[1]} does not match "
                f"expected {self.input_dim}"
            )

        return self.layers(x)

    def get_output_dim(self) -> int:
        """Returns the output embedding dimension."""
        return self.output_dim

    def get_input_dim(self) -> int:
        """Returns the input feature dimension."""
        return self.input_dim


def verify_projection_shape(config: Config, base_model_config: Optional[dict] = None) -> Tuple[int, int]:
    """
    Utility function to verify the projection layer dimensions without instantiating the full model.
    Useful for pre-flight checks in T015.

    Returns:
        Tuple of (input_dim, output_dim)
    """
    input_dim = config.feature_vector_size
    if input_dim is None or input_dim <= 0:
        raise ValueError(f"Invalid feature_vector_size: {input_dim}")

    if base_model_config:
        output_dim = base_model_config.get('hidden_size') or base_model_config.get('embedding_dim')
    else:
        output_dim = getattr(config, 'embedding_dim', None) or getattr(config, 'hidden_size', 768)

    if not output_dim:
        output_dim = 768

    return input_dim, output_dim