"""
Environment configuration management for dataset URLs and random seeds.

This module handles:
- Loading configuration from a YAML file (config/environment.yaml)
- Managing random seeds for reproducibility (numpy, random, torch if available)
- Providing dataset URLs and paths defined in the configuration
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import yaml
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_CONFIG_PATH = Path("code/config/environment.yaml")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class EnvironmentConfig:
    """Container for environment configuration settings."""

    def __init__(self, config_data: Dict[str, Any]):
        self.raw_config = config_data
        self.random_seed = config_data.get("random_seed", 42)
        self.datasets = config_data.get("datasets", {})
        self.paths = config_data.get("paths", {})
        self.experimental = config_data.get("experimental", {})

    def get_dataset_url(self, name: str) -> Optional[str]:
        """Get the URL for a specific dataset by name."""
        if name in self.datasets:
            return self.datasets[name].get("url")
        return None

    def get_dataset_path(self, name: str) -> Optional[Path]:
        """Get the local path for a specific dataset by name."""
        if name in self.datasets:
            relative_path = self.datasets[name].get("local_path")
            if relative_path:
                return PROJECT_ROOT / relative_path
        return None

    def get_path(self, key: str) -> Path:
        """Get a configured path by key."""
        relative_path = self.paths.get(key, "")
        if relative_path:
            return PROJECT_ROOT / relative_path
        return PROJECT_ROOT / key

    def is_experimental_feature_enabled(self, feature_name: str) -> bool:
        """Check if an experimental feature is enabled."""
        return self.experimental.get(feature_name, False)

    def __repr__(self) -> str:
        return (
            f"EnvironmentConfig(seed={self.random_seed}, "
            f"datasets={list(self.datasets.keys())})"
        )


def get_environment_config(config_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Load environment configuration from a YAML file.

    Args:
        config_path: Path to the configuration file. If None, uses DEFAULT_CONFIG_PATH.

    Returns:
        EnvironmentConfig instance with loaded settings.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the configuration file is not valid YAML.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        # If using relative path, try with PROJECT_ROOT
        full_path = PROJECT_ROOT / config_path
        if full_path.exists():
            config_path = full_path
        else:
            raise FileNotFoundError(
                f"Configuration file not found at {config_path} or {PROJECT_ROOT / config_path}"
            )

    logger.info(f"Loading environment configuration from {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    return EnvironmentConfig(config_data)


def initialize_random_seeds(seed: Optional[int] = None) -> None:
    """
    Initialize random seeds for reproducibility.

    This sets seeds for:
    - Python's random module
    - NumPy
    - PyTorch (if available)

    Args:
        seed: Random seed to use. If None, uses the seed from environment config.
    """
    if seed is None:
        try:
            config = get_environment_config()
            seed = config.random_seed
        except Exception as e:
            logger.warning(f"Could not load seed from config, using default 42: {e}")
            seed = 42

    logger.info(f"Initializing random seeds with value: {seed}")

    # Set seed for Python's random module
    random.seed(seed)

    # Set seed for NumPy
    np.random.seed(seed)

    # Set seed for PyTorch if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior (may impact performance)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        logger.info("PyTorch seeds initialized")
    except ImportError:
        logger.debug("PyTorch not available, skipping PyTorch seed initialization")

    # Set seed for TensorFlow if available
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        logger.info("TensorFlow seeds initialized")
    except ImportError:
        logger.debug("TensorFlow not available, skipping TensorFlow seed initialization")


def main() -> None:
    """Main function to demonstrate environment configuration usage."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # Load configuration
        config = get_environment_config()
        logger.info(f"Loaded configuration: {config}")

        # Initialize random seeds
        initialize_random_seeds()

        # Demonstrate dataset URL access
        gfa_url = config.get_dataset_url("gfa_recent")
        if gfa_url:
            logger.info(f"GFA Recent Dataset URL: {gfa_url}")
        else:
            logger.warning("GFA Recent Dataset URL not found in config")

        # Demonstrate path access
        data_dir = config.get_path("data_raw")
        logger.info(f"Data raw directory: {data_dir}")

        # Demonstrate experimental feature check
        if config.is_experimental_feature_enabled("use_weighted_models"):
            logger.info("Experimental feature 'use_weighted_models' is enabled")
        else:
            logger.info("Experimental feature 'use_weighted_models' is disabled")

    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
