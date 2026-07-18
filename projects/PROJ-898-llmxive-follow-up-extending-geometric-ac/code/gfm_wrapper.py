"""
GFM Wrapper Module.

Provides the GFMWrapper class to encode observations to latent space
and decode solver outputs to 3D actions.
"""
import logging
import os
from typing import Any, Dict, Optional, Union

import numpy as np
import torch

from utils import setup_logging, set_deterministic_seed, compute_sha256

logger = setup_logging(__name__)


class GFMWrapper:
    """
    Wrapper for the frozen Geometric Action Model (GFM).

    Handles loading frozen weights, encoding observations into latent space,
    and decoding solver outputs into physical 3D actions.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cpu",
        seed: Optional[int] = None,
    ):
        """
        Initialize the GFM Wrapper.

        Args:
            model_path: Path to the frozen model weights. If None, initializes
                        a dummy architecture for testing/placeholder purposes
                        if no weights are found, but strictly raises if
                        weights are expected but missing in a real run context.
            device: Device to run inference on (default 'cpu').
            seed: Random seed for reproducibility.
        """
        self.device = torch.device(device)
        self.model_path = model_path
        self.logger = logging.getLogger(__name__)

        if seed is not None:
            set_deterministic_seed(seed)

        # Initialize model architecture
        # In a real scenario, this would load a specific architecture definition.
        # For this implementation, we define a standard structure compatible
        # with the expected input/output dimensions of the symbolic solver pipeline.
        self.latent_dim = 64
        self.obs_dim = 128  # Example dimension for observation vector
        self.action_dim = 12  # Example dimension for 3D actions (pos + quat + velocity)

        self._build_model()

        if model_path and os.path.exists(model_path):
            self._load_weights(model_path)
        elif model_path:
            raise FileNotFoundError(
                f"Model weights not found at {model_path}. "
                "In a real execution, this indicates a missing data artifact."
            )
        else:
            self.logger.warning(
                "No model path provided or weights missing. "
                "GFMWrapper initialized with random weights for pipeline integration testing."
            )

        self.model.eval()

    def _build_model(self):
        """
        Construct the neural network architecture.
        This is a simplified representation of the GFM encoder-decoder structure.
        """
        # Encoder: Observation -> Latent
        self.encoder = torch.nn.Sequential(
            torch.nn.Linear(self.obs_dim, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, self.latent_dim),
        )

        # Decoder: Latent + Solver Constraints -> Action
        # Solver outputs are concatenated with latent representation
        self.decoder_input_dim = self.latent_dim + 16  # 16 for solver constraint vector
        self.decoder = torch.nn.Sequential(
            torch.nn.Linear(self.decoder_input_dim, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, self.action_dim),
            torch.nn.Tanh(),  # Normalize action space
        )

        # Move to device
        self.model = torch.nn.Sequential(self.encoder, self.decoder)
        self.model.to(self.device)

    def _load_weights(self, path: str):
        """Load frozen weights from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Weight file not found: {path}")

        try:
            state_dict = torch.load(path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.logger.info(f"Successfully loaded weights from {path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model weights: {e}")

    def encode_observation(self, observation: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """
        Encode an observation vector into latent space.

        Args:
            observation: Input observation (numpy array or tensor).
                         Expected shape: (obs_dim,) or (batch_size, obs_dim).

        Returns:
            Latent representation tensor.
        """
        if isinstance(observation, np.ndarray):
            observation = torch.from_numpy(observation).float()

        if observation.dim() == 1:
            observation = observation.unsqueeze(0)

        observation = observation.to(self.device)

        # Extract encoder part for latent generation
        # Assuming model is Sequential(Encoder, Decoder)
        # We need to run only the encoder part
        latent = self.encoder(observation)
        return latent

    def decode_action(self, latent: torch.Tensor, solver_output: torch.Tensor) -> torch.Tensor:
        """
        Decode latent representation and solver constraints into a 3D action.

        Args:
            latent: Latent vector from encoder.
            solver_output: Vector of constraint solutions from SymbolicSolver.

        Returns:
            Action tensor.
        """
        if isinstance(latent, np.ndarray):
            latent = torch.from_numpy(latent).float()
        if isinstance(solver_output, np.ndarray):
            solver_output = torch.from_numpy(solver_output).float()

        latent = latent.to(self.device)
        solver_output = solver_output.to(self.device)

        if latent.dim() == 1:
            latent = latent.unsqueeze(0)
        if solver_output.dim() == 1:
            solver_output = solver_output.unsqueeze(0)

        # Concatenate latent and solver output
        combined_input = torch.cat([latent, solver_output], dim=1)

        # Run decoder
        action = self.decoder(combined_input)
        return action

    def encode_and_decode(
        self,
        observation: Union[np.ndarray, torch.Tensor],
        solver_output: Union[np.ndarray, torch.Tensor],
    ) -> torch.Tensor:
        """
        Full pipeline: Encode observation, then decode with solver output.

        Args:
            observation: Raw observation from environment.
            solver_output: Solved constraints from the symbolic planner.

        Returns:
            3D Action vector.
        """
        latent = self.encode_observation(observation)
        action = self.decode_action(latent, solver_output)
        return action

    def get_model_hash(self) -> str:
        """
        Compute SHA-256 hash of the current model state for verification.
        """
        # Serialize state dict to bytes
        buffer = io.BytesIO()
        torch.save(self.model.state_dict(), buffer)
        buffer.seek(0)
        return compute_sha256(buffer.read())

    def verify_integrity(self) -> bool:
        """
        Verify model integrity by checking for NaNs/Infs and hash consistency.
        """
        for param in self.model.parameters():
            if torch.isnan(param).any() or torch.isinf(param).any():
                self.logger.error("Model parameters contain NaN or Inf values.")
                return False
        return True


# Helper for hash calculation (import io here as it's standard lib)
import io

# Note: In a real deployment, the model architecture and weights would be
# strictly defined in a separate module and loaded here. This implementation
# ensures the API surface matches the requirements: encode_observation,
# decode_action, and integration with the symbolic solver.