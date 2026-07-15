"""
Configuration management for the llmXive gravitational wave compression pipeline.

This module handles:
1. Random seed pinning for reproducibility across numpy, python, and torch (if available).
2. Path management for project directories (data, code, results) based on the project root.
3. Environment variable overrides for configuration values.
"""

import os
import random
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

# Attempt to import torch for reproducibility, but don't fail if missing
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Attempt to import numpy for reproducibility
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def set_global_seed(seed: int) -> None:
    """
    Set the random seed for all supported libraries to ensure reproducibility.

    Args:
        seed (int): The seed value to use.
    """
    if not isinstance(seed, int):
        raise ConfigError(f"Seed must be an integer, got {type(seed)}")

    # Python standard library
    random.seed(seed)

    # NumPy
    if HAS_NUMPY:
        np.random.seed(seed)

    # PyTorch (if available)
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False


def get_project_root() -> Path:
    """
    Determine the project root directory.

    Looks for a 'pyproject.toml' or '.git' directory to identify the root.
    Falls back to the current working directory if not found.

    Returns:
        Path: The absolute path to the project root.
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_data_dir(subdir: Optional[str] = None) -> Path:
    """
    Get the path to the data directory.

    Args:
        subdir (Optional[str]): Optional subdirectory within the data folder.

    Returns:
        Path: The absolute path to the data directory (or subdirectory).
    """
    root = get_project_root()
    data_path = root / "data"

    if subdir:
        data_path = data_path / subdir

    # Ensure the directory exists
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def get_code_dir(subdir: Optional[str] = None) -> Path:
    """
    Get the path to the code directory.

    Args:
        subdir (Optional[str]): Optional subdirectory within the code folder.

    Returns:
        Path: The absolute path to the code directory (or subdirectory).
    """
    root = get_project_root()
    code_path = root / "code"

    if subdir:
        code_path = code_path / subdir

    return code_path


def get_results_dir(subdir: Optional[str] = None) -> Path:
    """
    Get the path to the results/output directory.

    Args:
        subdir (Optional[str]): Optional subdirectory within the results folder.

    Returns:
        Path: The absolute path to the results directory (or subdirectory).
    """
    root = get_project_root()
    results_path = root / "results"

    if subdir:
        results_path = results_path / subdir

    results_path.mkdir(parents=True, exist_ok=True)
    return results_path


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value from environment variables.

    Args:
        key (str): The environment variable name.
        default (Any): Default value if the key is not found.

    Returns:
        Any: The value from the environment or the default.
    """
    return os.getenv(key, default)


def generate_run_id() -> str:
    """
    Generate a unique run ID based on the current timestamp and a random seed.

    Returns:
        str: A unique identifier string.
    """
    import time
    timestamp = str(int(time.time()))
    random_part = str(random.randint(1000, 9999))
    combined = f"{timestamp}_{random_part}"
    return hashlib.sha256(combined.encode()).hexdigest()[:12]


class PipelineConfig:
    """
    Central configuration class for the pipeline.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the pipeline configuration.

        Args:
            seed (Optional[int]): Random seed. If None, attempts to read from
                                  'RANDOM_SEED' env var, otherwise uses a default.
        """
        self._seed = seed
        if self._seed is None:
            env_seed = get_config_value("RANDOM_SEED")
            if env_seed:
                try:
                    self._seed = int(env_seed)
                except ValueError:
                    self._seed = 42
            else:
                self._seed = 42

        # Apply the seed
        set_global_seed(self._seed)

        # Paths
        self.root = get_project_root()
        self.data = get_data_dir()
        self.code = get_code_dir()
        self.results = get_results_dir()

        # Specific subdirectories
        self.raw_data = get_data_dir("raw")
        self.interim_data = get_data_dir("interim")
        self.processed_data = get_data_dir("processed")
        self.figures = get_data_dir("figures")
        self.reports = get_data_dir("reports")

    @property
    def seed(self) -> int:
        """The current random seed."""
        return self._seed

    def __repr__(self) -> str:
        return f"PipelineConfig(seed={self._seed}, root={self.root})"