"""
MLP Model for DelTA Coefficient Prediction (US2)

Implements a 2-layer Multi-Layer Perceptron using PyTorch.
Designed to run on CPU only, using static features (n-grams, POS, semantic similarity)
to predict DelTA coefficients.

Architecture:
  Input -> Linear(in_dim, hidden_dim) -> ReLU -> Linear(hidden_dim, 1)
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple

class DelTA_MLP(nn.Module):
    """
    A simple 2-layer MLP for predicting token-level DelTA coefficients.

    Args:
        input_dim (int): Dimension of the input feature vector.
        hidden_dim (int): Dimension of the hidden layer.
        dropout_rate (float): Dropout probability for regularization.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 256,
        dropout_rate: float = 0.1
    ):
        super(DelTA_MLP, self).__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        # Layer 1: Input -> Hidden
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout_rate)

        # Layer 2: Hidden -> Output (Single coefficient prediction)
        self.fc2 = nn.Linear(hidden_dim, 1)

        # Initialize weights for better convergence on CPU
        self._init_weights()

    def _init_weights(self) -> None:
        """Initialize weights using He initialization for ReLU activations."""
        for m in [self.fc1, self.fc2]:
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None:
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, input_dim).

        Returns:
            torch.Tensor: Predicted coefficients of shape (batch_size, 1).
        """
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.dropout1(x)
        x = self.fc2(x)
        return x

    def get_config(self) -> dict:
        """Return model configuration parameters."""
        return {
            "model_type": "DelTA_MLP",
            "input_dim": self.input_dim,
            "hidden_dim": self.hidden_dim,
            "dropout_rate": self.dropout1.p
        }

    @classmethod
    def from_config(cls, config: dict) -> 'DelTA_MLP':
        """Create model instance from configuration dictionary."""
        return cls(
            input_dim=config["input_dim"],
            hidden_dim=config.get("hidden_dim", 256),
            dropout_rate=config.get("dropout_rate", 0.1)
        )


def create_model(input_dim: int, hidden_dim: int = 256) -> DelTA_MLP:
    """
    Factory function to create a DelTA_MLP instance.

    Args:
        input_dim (int): Expected input feature dimension.
        hidden_dim (int): Hidden layer size (default 256 for moderate capacity).

    Returns:
        DelTA_MLP: Initialized model instance.
    """
    return DelTA_MLP(input_dim=input_dim, hidden_dim=hidden_dim)