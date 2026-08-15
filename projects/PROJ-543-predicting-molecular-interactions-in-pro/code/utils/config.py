"""
Environment configuration management for molecular interaction prediction.

This module handles seed setting for reproducibility and hyperparameter
management from YAML configuration files.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch
import yaml

# Default configuration file path relative to project root
DEFAULT_CONFIG_PATH = Path("code/config/experiment_config.yaml")


class ConfigManager:
    """
    Manages experiment configuration, including random seeds and hyperparameters.

    Attributes:
        config (Dict[str, Any]): The loaded configuration dictionary.
        config_path (Path): Path to the configuration file.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initializes the ConfigManager.

        Args:
            config_path: Optional path to the configuration file. Defaults to
                         DEFAULT_CONFIG_PATH if not provided.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}

        if self.config_path.exists():
            self._load_config()
        else:
            # Provide a sensible default if no config file exists
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Returns a default configuration dictionary.

        Returns:
            A dictionary with default values for seeds and hyperparameters.
        """
        return {
            "seed": 42,
            "hyperparameters": {
                "hidden_channels": 128,
                "num_layers": 3,
                "dropout": 0.1,
                "learning_rate": 1e-3,
                "batch_size": 32,
                "epochs": 100,
                "patience": 10,
                "cutoff_distance": 5.0,
                "water_cutoff": 3.5,
                "resolution_threshold": 2.5,
            },
            "paths": {
                "data_raw": "data/raw",
                "data_processed": "data/processed",
                "data_results": "data/results",
                "figures": "figures",
            },
        }

    def _load_config(self) -> None:
        """
        Loads the configuration from the YAML file.

        Raises:
            FileNotFoundError: If the config file does not exist.
            yaml.YAMLError: If the YAML file is malformed.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            try:
                self.config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML config: {e}")

        # Ensure expected keys exist, filling with defaults if necessary
        self.config.setdefault("seed", 42)
        self.config.setdefault("hyperparameters", self._get_default_config()["hyperparameters"])
        self.config.setdefault("paths", self._get_default_config()["paths"])

    def set_seeds(self) -> None:
        """
        Sets random seeds for reproducibility across Python, NumPy, and PyTorch.

        This ensures that results are reproducible across runs with the same
        configuration.
        """
        seed = self.config.get("seed", 42)

        # Python's random
        random.seed(seed)

        # NumPy
        np.random.seed(seed)

        # PyTorch (CPU and CUDA)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior for CUDA operations
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

        # Set environment variable for additional determinism (optional but recommended)
        os.environ["PYTHONHASHSEED"] = str(seed)

    def get_hyperparameter(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a specific hyperparameter value.

        Args:
            key: The key of the hyperparameter to retrieve.
            default: The default value to return if the key is not found.

        Returns:
            The value of the hyperparameter, or the default if not found.
        """
        return self.config.get("hyperparameters", {}).get(key, default)

    def get_path(self, key: str, default: Any = None) -> Path:
        """
        Retrieves a specific path configuration value.

        Args:
            key: The key of the path to retrieve.
            default: The default value to return if the key is not found.

        Returns:
            The value of the path, or the default if not found.
        """
        path_str = self.config.get("paths", {}).get(key, default)
        return Path(path_str) if path_str else default

    def save_config(self, path: Optional[Path] = None) -> None:
        """
        Saves the current configuration to a YAML file.

        Args:
            path: Optional path to save the configuration. Defaults to
                  config_path if not provided.
        """
        save_path = path or self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False)


def initialize_experiment(config_path: Optional[Path] = None) -> ConfigManager:
    """
    Convenience function to initialize the experiment configuration.

    This function creates a ConfigManager instance and sets all necessary
    random seeds.

    Args:
        config_path: Optional path to the configuration file.

    Returns:
        An initialized ConfigManager instance.
    """
    config_manager = ConfigManager(config_path)
    config_manager.set_seeds()
    return config_manager
