"""
Random seed management utility for reproducible scientific computing.

This module provides a centralized interface for setting and managing
random seeds across all major Python libraries used in this project
(random, numpy, scipy, torch, etc.) to ensure deterministic execution
of statistical analyses.
"""
import os
import random
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union, Generator, List

# Optional imports for libraries that may be installed
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

try:
    import scipy
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from config import get_project_root

# Constants
DEFAULT_SEED = 42
SEED_CONFIG_FILENAME = "seed_config.json"
SEED_CONFIG_PATH = get_project_root() / "artifacts" / SEED_CONFIG_FILENAME


class SeedManager:
    """
    Centralized manager for random seed generation and propagation.

    This class handles:
    - Generation of reproducible seeds
    - Setting seeds across all supported libraries
    - Saving/loading seed configurations for audit trails
    - Context management for temporary seed changes
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the SeedManager.

        Args:
            seed: Optional integer seed. If None, generates a new seed.
        """
        self._seed = seed if seed is not None else self._generate_seed()
        self._config_path = SEED_CONFIG_PATH
        self._ensure_artifacts_dir()

    def _ensure_artifacts_dir(self) -> None:
        """Ensure the artifacts directory exists."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_seed() -> int:
        """
        Generate a new random seed.

        Returns:
            A random integer between 0 and 2^32-1.
        """
        return random.getrandbits(32)

    @property
    def seed(self) -> int:
        """Get the current seed value."""
        return self._seed

    @seed.setter
    def seed(self, value: int) -> None:
        """Set the current seed value."""
        if not isinstance(value, int) or value < 0 or value > 2**32 - 1:
            raise ValueError(f"Seed must be a non-negative integer <= {2**32-1}")
        self._seed = value

    def set_all_seeds(self, seed: Optional[int] = None) -> None:
        """
        Set seeds for all supported libraries to ensure reproducibility.

        Args:
            seed: Optional seed value. If None, uses the manager's current seed.
        """
        current_seed = seed if seed is not None else self._seed

        # Python random
        random.seed(current_seed)

        # NumPy
        if HAS_NUMPY:
            np.random.seed(current_seed)
            # For newer numpy versions (1.17+), also set the Generator
            np.random.default_rng(current_seed)

        # PyTorch
        if HAS_TORCH:
            torch.manual_seed(current_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(current_seed)
                torch.cuda.manual_seed_all(current_seed)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False

        # TensorFlow
        if HAS_TENSORFLOW:
            tf.random.set_seed(current_seed)

        # Scipy
        # Scipy mostly relies on numpy's random state, so no direct seed setting needed
        # but we ensure numpy is set (done above)

    def save_config(self, metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Save the current seed configuration to disk.

        Args:
            metadata: Optional dictionary of metadata to include (e.g., script name, timestamp).

        Returns:
            Path to the saved configuration file.
        """
        config = {
            "seed": self._seed,
            "hash": hashlib.sha256(str(self._seed).encode()).hexdigest()[:16],
            "libraries": {
                "python_random": True,
                "numpy": HAS_NUMPY,
                "torch": HAS_TORCH,
                "tensorflow": HAS_TENSORFLOW,
                "scipy": HAS_SCIPY
            },
            "metadata": metadata or {}
        }

        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        return self._config_path

    @classmethod
    def load_config(cls, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Load a seed configuration from disk.

        Args:
            config_path: Path to the configuration file. If None, uses the default path.

        Returns:
            Dictionary containing the seed configuration.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
        """
        path = Path(config_path) if config_path else cls._config_path
        if not path.exists():
            raise FileNotFoundError(f"Seed configuration not found at {path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def from_config(cls, config_path: Optional[Union[str, Path]] = None) -> 'SeedManager':
        """
        Create a SeedManager instance from a saved configuration.

        Args:
            config_path: Path to the configuration file.

        Returns:
            A new SeedManager instance initialized with the saved seed.
        """
        config = cls.load_config(config_path)
        return cls(seed=config["seed"])


def set_seed(seed: Optional[int] = None) -> int:
    """
    Convenience function to set seeds for all libraries.

    Args:
        seed: Optional seed value. If None, generates a new seed.

    Returns:
        The seed value that was set.
    """
    manager = SeedManager(seed)
    manager.set_all_seeds()
    return manager.seed


def get_seed() -> Optional[int]:
    """
    Get the current seed value from the global state.

    Returns:
        The current seed if set, otherwise None.
    """
    # Try to read from the config file if it exists
    if SEED_CONFIG_PATH.exists():
        try:
            config = SeedManager.load_config()
            return config.get("seed")
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def generate_seed() -> int:
    """
    Generate a new random seed without setting it.

    Returns:
        A new random integer seed.
    """
    return random.getrandbits(32)


def save_seed_config(seed: int, metadata: Optional[Dict[str, Any]] = None) -> Path:
    """
    Save a seed configuration to disk.

    Args:
        seed: The seed value to save.
        metadata: Optional metadata dictionary.

    Returns:
        Path to the saved configuration file.
    """
    manager = SeedManager(seed)
    return manager.save_config(metadata)


def load_seed_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load a seed configuration from disk.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Dictionary containing the seed configuration.
    """
    return SeedManager.load_config(config_path)


class SeedContext:
    """
    Context manager for temporary seed changes.

    Usage:
        with SeedContext(123):
            # Code that needs a specific seed
            pass
        # Seed is restored to previous state after exit
    """

    def __init__(self, seed: int):
        """
        Initialize the context manager.

        Args:
            seed: The seed to use within the context.
        """
        self._seed = seed
        self._original_seed = None

    def __enter__(self) -> int:
        """Save current state and set new seed."""
        # Save current random state
        self._original_seed = get_seed()
        set_seed(self._seed)
        return self._seed

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Restore original seed."""
        if self._original_seed is not None:
            set_seed(self._original_seed)


def get_random_state() -> Dict[str, Any]:
    """
    Capture the current random state of all libraries.

    Returns:
        Dictionary containing the current random states.
    """
    state = {
        "python_random": random.getstate()
    }

    if HAS_NUMPY:
        state["numpy"] = np.random.get_state()

    if HAS_TORCH:
        state["torch_cpu"] = torch.get_rng_state()
        if torch.cuda.is_available():
            state["torch_cuda"] = torch.cuda.get_rng_state_all()

    return state


def main() -> None:
    """Command-line interface for seed management utilities."""
    import argparse

    parser = argparse.ArgumentParser(description="Random seed management utility")
    parser.add_argument(
        "--action",
        choices=["generate", "set", "save", "load", "show"],
        default="generate",
        help="Action to perform"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed value (required for 'set' and 'save' actions)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to seed config file (for 'load' action)"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        help="JSON string of metadata to save with seed"
    )

    args = parser.parse_args()

    if args.action == "generate":
        new_seed = generate_seed()
        print(f"Generated new seed: {new_seed}")

    elif args.action == "set":
        if args.seed is None:
            parser.error("--seed is required for 'set' action")
        set_seed(args.seed)
        print(f"Set global seed to: {args.seed}")

    elif args.action == "save":
        if args.seed is None:
            parser.error("--seed is required for 'save' action")
        metadata = json.loads(args.metadata) if args.metadata else None
        path = save_seed_config(args.seed, metadata)
        print(f"Saved seed configuration to: {path}")

    elif args.action == "load":
        config = load_seed_config(args.config)
        print(json.dumps(config, indent=2))

    elif args.action == "show":
        seed = get_seed()
        if seed is not None:
            print(f"Current seed: {seed}")
        else:
            print("No seed currently set")


if __name__ == "__main__":
    main()