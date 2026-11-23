"""
MLP Model for predicting scaling factors from statistical moments.

Implements FR-009: Define a multi-layer perceptron (MLP) model architecture 
with statistical moment features (mean, variance).

Input Features:
  - mean: Mean of the attention matrix
  - variance: Variance of the attention matrix

Output:
  - scaling_factor: Predicted scaling factor (float)
"""

import torch
import torch.nn as nn
from typing import Tuple


class StaticPriorMLP(nn.Module):
    """
    Multi-Layer Perceptron for static prior prediction.
    
    Architecture designed for CPU efficiency and small input dimensionality (2 features).
    Input: [mean, variance]
    Output: scaling_factor
    
    Requirements Satisfied:
      - Input (mean, variance) -> Hidden layer -> Hidden layer -> Output (scalar)
      - Xavier initialization
      - MSE loss and Adam optimizer (handled in training loop, but architecture supports it)
      - Fixed 2-feature input as per Spec FR-002
    """
    
    def __init__(
        self,
        input_dim: int = 2,
        hidden_dims: Tuple[int, ...] = (32, 16),
        output_dim: int = 1,
        dropout_rate: float = 0.0
    ):
        """
        Initialize the MLP model with Xavier initialization.
        
        Args:
            input_dim: Number of input features (default 2: mean, variance)
            hidden_dims: Tuple of hidden layer sizes
            output_dim: Number of output features (default 1: scaling_factor)
            dropout_rate: Dropout probability for regularization (default 0.0)
        """
        super(StaticPriorMLP, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim
        
        # Build the network layers dynamically
        layers = []
        prev_dim = input_dim
        
        for i, hidden_dim in enumerate(hidden_dims):
            layers.append(nn.Linear(prev_dim, hidden_dim))
            # Xavier initialization is applied via nn.init.xavier_uniform_ below
            # ReLU activation
            layers.append(nn.ReLU())
            # Optional dropout
            if dropout_rate > 0.0:
                layers.append(nn.Dropout(dropout_rate))
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, output_dim))
        
        self.network = nn.Sequential(*layers)
        
        # Initialize weights using Xavier (Glorot) initialization as required
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights using Xavier (Glorot) uniform initialization."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, input_dim)
        
        Returns:
            Output tensor of shape (batch_size, output_dim)
        """
        # Ensure input is 2D
        if x.dim() == 1:
            x = x.unsqueeze(0)
        
        return self.network(x)
    
    def predict(self, mean: float, variance: float) -> float:
        """
        Predict scaling factor for a single input.
        
        Args:
            mean: Mean of the attention matrix
            variance: Variance of the attention matrix
        
        Returns:
            Predicted scaling factor
        """
        self.eval()
        with torch.no_grad():
            x = torch.tensor([[float(mean), float(variance)]], dtype=torch.float32)
            output = self.forward(x)
            return output.item()
    
    def get_feature_dim(self) -> int:
        """Return the expected input feature dimension."""
        return self.input_dim


def create_model(config: dict = None) -> StaticPriorMLP:
    """
    Factory function to create an MLP model with optional configuration.
    
    Args:
        config: Optional dictionary with model configuration
            - input_dim: int (default 2)
            - hidden_dims: Tuple[int] (default (32, 16))
            - output_dim: int (default 1)
            - dropout_rate: float (default 0.0)
    
    Returns:
        Configured StaticPriorMLP instance
    """
    if config is None:
        config = {}
    
    return StaticPriorMLP(
        input_dim=config.get('input_dim', 2),
        hidden_dims=config.get('hidden_dims', (32, 16)),
        output_dim=config.get('output_dim', 1),
        dropout_rate=config.get('dropout_rate', 0.0)
    )

# Default model instance for convenience
default_model = create_model()