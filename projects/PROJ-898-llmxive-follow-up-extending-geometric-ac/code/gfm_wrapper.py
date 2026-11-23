"""
Wrapper for the Geometric Function Model (GFM).
Handles loading frozen weights and performing inference.

Supports two modes:
  - "frozen": autograd fully disabled (default, used for evaluation).
  - "diff":   autograd enabled on INPUTS only, for finite-difference
              verification of the symbolic solver. Weights remain
              frozen (requires_grad=False) in both modes.
"""
import logging
import os
from typing import Optional, Union
import numpy as np
import torch
import torch.nn as nn

from .utils import setup_logging, set_deterministic_seed, compute_sha256


class GFMWrapper(nn.Module):
    """
    Wrapper for the Geometric Function Model.
    Loads frozen weights and provides encode/decode methods.
    """

    VALID_MODES = ("frozen", "diff")

    def __init__(
        self,
        weights_path: str,
        latent_dim: int = 64,
        obs_dim: int = 128,
        action_dim: int = 7,
        mode: str = "frozen",
    ):
        """
        Initialize the GFM wrapper.

        Args:
            weights_path: Path to the frozen weights file.
            latent_dim: Dimension of the latent space.
            obs_dim: Dimension of the observation input.
            action_dim: Dimension of the action output.
            mode: "frozen" (no autograd anywhere) or "diff"
                (autograd enabled on inputs for finite-difference
                verification; weights stay frozen).
        """
        super().__init__()

        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of {self.VALID_MODES}."
            )
        self.mode = mode

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
            logging.warning(
                f"Weights file not found at {weights_path}. "
                "Using random initialization."
            )

        # Freeze all parameters (both modes)
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

    def _prepare_input(
        self, x: Union[np.ndarray, torch.Tensor]
    ) -> torch.Tensor:
        """Convert input to a float tensor, enabling autograd in diff mode."""
        if isinstance(x, np.ndarray):
            x = torch.from_numpy(x).float()
        else:
            x = x.float()

        if x.dim() == 1:
            x = x.unsqueeze(0)

        if self.mode == "diff" and not x.requires_grad:
            x = x.requires_grad_(True)

        return x

    def encode(self, observations: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """
        Encode observations into latent space.

        Args:
            observations: Input observations of shape (batch_size, obs_dim).

        Returns:
            Latent vectors of shape (batch_size, latent_dim).
        """
        observations = self._prepare_input(observations)

        if self.mode == "frozen":
            with torch.no_grad():
                latents = self.encoder(observations)
        else:
            # Diff mode: gradients flow through the input, not weights.
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
        latents = self._prepare_input(latents)

        if self.mode == "frozen":
            with torch.no_grad():
                actions = self.decoder(latents)
        else:
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

    def verify_gradient_flow(
        self, observations: Union[np.ndarray, torch.Tensor]
    ) -> dict:
        """
        Verify that gradients flow through inputs but not weights.

        Runs a forward/backward pass in diff mode and reports whether
        the input received a non-None, non-zero gradient while every
        model parameter gradient is None or zero.

        Args:
            observations: Input observations of shape (batch_size, obs_dim).

        Returns:
            Dict with 'input_grad_nonzero' and 'weights_frozen' booleans.
        """
        if self.mode != "diff":
            raise RuntimeError(
                "verify_gradient_flow requires mode='diff'."
            )

        x = self._prepare_input(observations)
        actions = self.decode(self.encode(x))
        loss = actions.sum()
        loss.backward()

        input_grad_nonzero = (
            x.grad is not None and bool(torch.any(x.grad != 0))
        )

        weights_frozen = True
        for param in self.parameters():
            if param.grad is not None and bool(torch.any(param.grad != 0)):
                weights_frozen = False
                break

        return {
            "input_grad_nonzero": input_grad_nonzero,
            "weights_frozen": weights_frozen,
        }
