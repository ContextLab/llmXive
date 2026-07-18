"""
CPU-Optimized Autoencoder Architecture (T014).

Implements a Multi-Layer Perceptron (MLP) based autoencoder with ReLU activations.
Designed to compress high-dimensional embeddings into configurable latent dimensions.
"""
import torch
import torch.nn as nn
from typing import List

class Autoencoder(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int, hidden_dims: List[int] = None):
        """
        Initializes the Autoencoder.

        Args:
            input_dim: Dimensionality of the input embeddings.
            latent_dim: Target dimensionality for the compressed vector.
            hidden_dims: List of dimensions for hidden layers. If None, defaults to
                         proportional layers based on input_dim.
        """
        super(Autoencoder, self).__init__()

        self.input_dim = input_dim
        self.latent_dim = latent_dim

        if hidden_dims is None:
            # Default proportional hidden layers: e.g., input -> input/2 -> input/4 -> latent
            # Ensuring we don't go below latent_dim in the encoder
            intermediate = max(latent_dim, input_dim // 2)
            hidden_dims = [input_dim // 2, intermediate]
            # Filter out dimensions smaller than latent_dim to avoid bottleneck issues
            hidden_dims = [d for d in hidden_dims if d >= latent_dim]

        # Encoder
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(h_dim)) # Optional stability
            prev_dim = h_dim
        # Final encoder layer to latent
        layers.append(nn.Linear(prev_dim, latent_dim))
        self.encoder = nn.Sequential(*layers)

        # Decoder (Reverse of encoder)
        decoder_layers = []
        prev_dim = latent_dim
        # Reverse hidden dims, but exclude the last one if it matches input_dim logic
        # We need to go from latent -> ... -> input
        reversed_hidden = list(reversed(hidden_dims))
        
        for h_dim in reversed_hidden:
            decoder_layers.append(nn.Linear(prev_dim, h_dim))
            decoder_layers.append(nn.ReLU())
            decoder_layers.append(nn.BatchNorm1d(h_dim))
            prev_dim = h_dim
        
        # Final decoder layer to input_dim
        decoder_layers.append(nn.Linear(prev_dim, input_dim))
        # No activation at the end for regression-like reconstruction (or Sigmoid if normalized 0-1)
        # Assuming embeddings are not strictly 0-1, we leave it linear or use Tanh if bounded.
        # Standard practice for embeddings is often linear.
        self.decoder = nn.Sequential(*decoder_layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstruction = self.decoder(latent)
        return reconstruction

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)

    def decode(self, latent: torch.Tensor) -> torch.Tensor:
        return self.decoder(latent)
