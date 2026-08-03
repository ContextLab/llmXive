"""
Wrapper for the Geometric Function Model (GFM).
Handles loading frozen weights and performing inference.
"""
import logging
import os
from typing import Any, Dict, Optional, Union
import numpy as np
import torch
import torch.nn as nn

from .utils import setup_logging, set_deterministic_seed, compute_sha256


class GFMWrapper(nn.Module):
    """
    Wrapper for the Geometric Function Model.
    Loads frozen weights and provides encode/decode methods.
    """

    def __init__(
        self,
        weights_path: str,
        latent_dim: int = 64,
        obs_dim: int = 128,
        action_dim: int = 7
    ):
        """
        Initialize the GFM wrapper.

        Args:
            weights_path: Path to the frozen weights file.
            latent_dim: Dimension of the latent space.
            obs_dim: Dimension of the observation input.
            action_dim: Dimension of the action output.
        """
        super().__init__()

        self.latent_dim = latent_dim
        self.obs_dim = obs_dim
        self.action_dim = action_dim

        # Define encoder architecture (simplified for demonstration)
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, latent_dim)
        )

        # Define decoder architecture (simplified for demonstration)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim),
            nn.Tanh()  # Actions typically in [-1, 1]
        )

        # Load weights if provided
        if os.path.exists(weights_path):
            self._load_weights(weights_path)
        else:
            logging.warning(f"Weights file not found at {weights_path}. Using random initialization.")

        # Freeze all parameters
        self._freeze_parameters()

        # Set to eval mode
        self.eval()

    def _load_weights(self, path: str) -> None:
        """Load weights from a file."""
        logger = setup_logging()
        logger.info(f"Loading GFM weights from {path}")

        try:
            checkpoint = torch.load(path, map_location='cpu')
            self.load_state_dict(checkpoint['state_dict'], strict=False)
            logger.info("Weights loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load weights: {e}")
            raise

    def _freeze_parameters(self) -> None:
        """Freeze all model parameters."""
        for param in self.parameters():
            param.requires_grad = False

    def encode(self, observations: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """
        Encode observations into latent space.

        Args:
            observations: Input observations of shape (batch_size, obs_dim).

        Returns:
            Latent vectors of shape (batch_size, latent_dim).
        """
        if isinstance(observations, np.ndarray):
            observations = torch.from_numpy(observations).float()

        if observations.dim() == 1:
            observations = observations.unsqueeze(0)

        with torch.no_grad():
            latents = self.encoder(observations)

        return latents

    def decode(self, latents: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """
        Decode latent vectors into actions.

        Args:
            latents: Latent vectors of shape (batch_size, latent_dim).

        Returns:
            Actions of shape (batch_size, action_dim).
        """
        if isinstance(latents, np.ndarray):
            latents = torch.from_numpy(latents).float()

        if latents.dim() == 1:
            latents = latents.unsqueeze(0)

        with torch.no_grad():
            actions = self.decoder(latents)

        return actions

    def forward(self, observations: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """
        Full forward pass: encode -> decode.

        Args:
            observations: Input observations.

        Returns:
            Decoded actions.
        """
        latents = self.encode(observations)
        actions = self.decode(latents)
        return actions
