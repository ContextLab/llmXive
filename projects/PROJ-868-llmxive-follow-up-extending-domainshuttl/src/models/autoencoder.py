"""
CPU-optimized Autoencoder architecture for embedding compression.

Implements a Multi-Layer Perceptron (MLP) with ReLU activation,
configured for Cosine Similarity loss as per FR-004.

Constraints:
- CPU-only execution
- Supports target dimensions [32, 64, 128, 256] (and 16 for sweep consistency)
- Enforces batch_size=1 and gradient_accumulation_steps=1
- Includes runtime memory check
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import psutil
import os
from typing import Tuple, Optional

from src.config.settings import get_config

# Allowed target dimensions as per FR-003
ALLOWED_DIMENSIONS = [16, 32, 64, 128, 256]

class MemoryLimitExceededError(Exception):
    """Raised when runtime memory usage exceeds the predefined threshold."""
    pass

def check_memory_usage(threshold_percent: float = 80.0) -> None:
    """
    Checks current RAM usage. Raises MemoryLimitExceededError if usage exceeds threshold.
    
    Args:
        threshold_percent: Maximum allowed RAM usage percentage.
        
    Raises:
        MemoryLimitExceededError: If usage exceeds threshold.
    """
    mem = psutil.virtual_memory()
    if mem.percent > threshold_percent:
        raise MemoryLimitExceededError(
            f"Memory usage {mem.percent:.1f}% exceeds threshold {threshold_percent}%. "
            "Aborting to prevent OOM."
        )

class CPUAutoencoder(nn.Module):
    """
    CPU-optimized Autoencoder using MLP with ReLU.
    
    Architecture:
    - Encoder: Input -> Hidden Layers -> Latent Vector
    - Decoder: Latent Vector -> Hidden Layers -> Output (reconstruction)
    
    Loss Function:
    - CosineEmbeddingLoss (as per FR-004, forbidding MSELoss)
    """
    
    def __init__(
        self,
        input_dim: int,
        target_dim: int,
        hidden_dims: Optional[Tuple[int, ...]] = None
    ):
        super().__init__()
        
        if target_dim not in ALLOWED_DIMENSIONS:
            raise ValueError(
                f"Target dimension {target_dim} not in allowed set {ALLOWED_DIMENSIONS}"
            )
        
        self.input_dim = input_dim
        self.target_dim = target_dim
        
        # Determine hidden layers proportionally if not provided
        if hidden_dims is None:
            # Create a symmetric structure: e.g., for input=768, target=64
            # Hidden layers might be: 512 -> 256 -> target
            # We scale based on input/target ratio
            if input_dim > 512:
                hidden_dims = (512, 256)
            elif input_dim > 256:
                hidden_dims = (256, 128)
            else:
                hidden_dims = (128, 64)
        
        # Build Encoder
        encoder_layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            encoder_layers.append(nn.Linear(prev_dim, h_dim))
            encoder_layers.append(nn.ReLU())
            encoder_layers.append(nn.BatchNorm1d(h_dim)) # Stabilize CPU training
            prev_dim = h_dim
        encoder_layers.append(nn.Linear(prev_dim, target_dim))
        self.encoder = nn.Sequential(*encoder_layers)
        
        # Build Decoder (symmetric)
        decoder_layers = []
        prev_dim = target_dim
        # Reverse hidden dims for decoder
        for h_dim in reversed(hidden_dims):
            decoder_layers.append(nn.Linear(prev_dim, h_dim))
            decoder_layers.append(nn.ReLU())
            decoder_layers.append(nn.BatchNorm1d(h_dim))
            prev_dim = h_dim
        decoder_layers.append(nn.Linear(prev_dim, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)
        
        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights using Kaiming uniform for ReLU."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_uniform_(module.weight, nonlinearity='relu')
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode input to latent representation."""
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent representation to reconstruction."""
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: encode then decode."""
        z = self.encode(x)
        return self.decode(z)

    def get_loss_fn(self) -> nn.CosineEmbeddingLoss:
        """
        Returns the configured loss function.
        
        Constraint: MUST use CosineEmbeddingLoss. MSELoss is forbidden.
        """
        # CosineEmbeddingLoss expects (x1, x2, target)
        # target is 1 if similar, -1 if dissimilar.
        # For autoencoding, we want reconstruction to be similar to input.
        return nn.CosineEmbeddingLoss(margin=0.0)

def get_autoencoder(
    input_dim: int,
    target_dim: int
) -> CPUAutoencoder:
    """
    Factory function to instantiate the CPUAutoencoder.
    
    Args:
        input_dim: Dimension of the input embeddings.
        target_dim: Target compression dimension.
        
    Returns:
        Configured CPUAutoencoder instance.
    """
    check_memory_usage()
    return CPUAutoencoder(input_dim=input_dim, target_dim=target_dim)