"""
Environment configuration management for the Quantum Cognition in LLMs project.

Provides centralized configuration for:
- Random seed pinning for reproducibility
- Device selection (CPU-only enforced)
- Batch size configuration
- Other experiment hyperparameters
"""
import os
import random
import torch
import numpy as np
from typing import Optional, Dict, Any


class Config:
    """Centralized configuration class for experiment parameters."""

    # Default values
    DEFAULT_SEED: int = 42
    DEFAULT_DEVICE: str = "cpu"
    DEFAULT_BATCH_SIZE: int = 8
    DEFAULT_NUM_WORKERS: int = 0  # CPU-only, avoid multiprocessing overhead issues
    DEFAULT_MAX_LENGTH: int = 128
    DEFAULT_LEARNING_RATE: float = 1e-4
    DEFAULT_NUM_EPOCHS: int = 3
    DEFAULT_LAMBDA_PHASE: float = 0.5  # For phase penalty in FR-009

    def __init__(
        self,
        seed: Optional[int] = None,
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
        num_workers: Optional[int] = None,
        max_length: Optional[int] = None,
        learning_rate: Optional[float] = None,
        num_epochs: Optional[int] = None,
        lambda_phase: Optional[float] = None,
    ):
        """
        Initialize configuration with optional overrides.

        Args:
            seed: Random seed for reproducibility. Defaults to 42.
            device: Compute device ("cpu" only enforced). Defaults to "cpu".
            batch_size: Batch size for training/inference. Defaults to 8.
            num_workers: DataLoader workers. Defaults to 0 for CPU-only.
            max_length: Maximum sequence length. Defaults to 128.
            learning_rate: Learning rate for optimizer. Defaults to 1e-4.
            num_epochs: Number of training epochs. Defaults to 3.
            lambda_phase: Lambda for phase penalty term. Defaults to 0.5.
        """
        self.seed = seed if seed is not None else self.DEFAULT_SEED
        self.device = self._validate_device(device)
        self.batch_size = batch_size if batch_size is not None else self.DEFAULT_BATCH_SIZE
        self.num_workers = num_workers if num_workers is not None else self.DEFAULT_NUM_WORKERS
        self.max_length = max_length if max_length is not None else self.DEFAULT_MAX_LENGTH
        self.learning_rate = learning_rate if learning_rate is not None else self.DEFAULT_LEARNING_RATE
        self.num_epochs = num_epochs if num_epochs is not None else self.DEFAULT_NUM_EPOCHS
        self.lambda_phase = lambda_phase if lambda_phase is not None else self.DEFAULT_LAMBDA_PHASE

        # Pin all random seeds
        self._pin_seeds()

    def _validate_device(self, device: Optional[str]) -> str:
        """
        Validate and enforce CPU-only device selection.

        Args:
            device: Requested device string.

        Returns:
            Validated device string (always "cpu").

        Raises:
            ValueError: If a non-CPU device is requested.
        """
        if device is None:
            return self.DEFAULT_DEVICE

        device = device.lower()
        if device != "cpu":
            raise ValueError(
                f"GPU devices are not supported in this CPU-only environment. "
                f"Requested: {device}, but only 'cpu' is allowed."
            )
        return "cpu"

    def _pin_seeds(self) -> None:
        """Pin all random number generator seeds for reproducibility."""
        # Set Python random seed
        random.seed(self.seed)

        # Set NumPy random seed
        np.random.seed(self.seed)

        # Set PyTorch random seeds
        torch.manual_seed(self.seed)
        torch.cuda.manual_seed_all(self.seed)  # No-op on CPU, but safe to call
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

        # Set environment variable for deterministic behavior
        os.environ["PYTHONHASHSEED"] = str(self.seed)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "seed": self.seed,
            "device": self.device,
            "batch_size": self.batch_size,
            "num_workers": self.num_workers,
            "max_length": self.max_length,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "lambda_phase": self.lambda_phase,
        }

    def __repr__(self) -> str:
        """String representation of the configuration."""
        return f"Config(seed={self.seed}, device={self.device}, batch_size={self.batch_size})"


def get_config(
    seed: Optional[int] = None,
    device: Optional[str] = None,
    batch_size: Optional[int] = None,
    **overrides
) -> Config:
    """
    Factory function to create a Config instance.

    Args:
        seed: Random seed for reproducibility.
        device: Compute device (must be "cpu").
        batch_size: Batch size for training/inference.
        **overrides: Additional keyword arguments to override defaults.

    Returns:
        Config instance with pinned seeds and validated parameters.
    """
    return Config(
        seed=seed,
        device=device,
        batch_size=batch_size,
        **overrides
    )


def set_environment() -> None:
    """
    Set up environment variables for deterministic behavior.
    Call this at the start of any experiment script.
    """
    os.environ["PYTHONHASHSEED"] = str(Config.DEFAULT_SEED)
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":16:8"