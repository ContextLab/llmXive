"""
Configuration loader for random seeds and path constants.

This module provides a centralized configuration management system for the llmXive
gene regulation analysis pipeline. It handles:
- Random seed management for reproducibility
- Path constants for all project directories
- Environment variable overrides
- Configuration validation
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml

from utils.logging import get_logger, ConfigurationError

logger = get_logger(__name__)

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default configuration values
DEFAULT_CONFIG = {
    "random_seed": 42,
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "outputs_reports": "outputs/reports",
        "outputs_figures": "outputs/figures",
        "state": "state",
        "specs": "specs",
        "code": "code"
    },
    "model": {
        "n_folds": 5,
        "n_estimators_rf": 100,
        "max_depth_rf": 5,
        "alpha_lasso": 0.1,
        "l1_ratio_elastic_net": 0.5,
        "max_iter": 10000
    },
    "analysis": {
        "permutation_iterations": 1000,
        "sensitivity_threshold_range": [0.3, 0.9],
        "sensitivity_step": 0.05
    },
    "data": {
        "geneb_repo": "genomics-benchmark/geneb",
        "zenodo_record_id": "1234567",  # Placeholder, to be updated with real ID
        "max_workers": 4,
        "retry_attempts": 3,
        "retry_backoff_factor": 2.0
    },
    "validation": {
        "entropy_floor": 1e-6,
        "mcc_min": -1.0,
        "mcc_max": 1.0,
        "high_performance_threshold": 0.6
    }
}

CONFIG_FILE_PATH = PROJECT_ROOT / "config.yaml"
CONFIG_SCHEMA_PATH = PROJECT_ROOT / "specs/gene-regulation/contracts/config.schema.yaml"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return defaults.

    Args:
        config_path: Optional path to a custom config file. If None, uses CONFIG_FILE_PATH.

    Returns:
        Dictionary containing the complete configuration.

    Raises:
        ConfigurationError: If the config file is invalid or cannot be parsed.
    """
    path = config_path or CONFIG_FILE_PATH
    config = DEFAULT_CONFIG.copy()

    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}
            _deep_merge(config, user_config)
            logger.info(f"Loaded configuration from {path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse config file {path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading config file {path}: {e}")
    else:
        logger.info(f"No custom config found at {path}, using defaults.")

    # Override with environment variables if present
    _apply_env_overrides(config)

    _validate_config(config)
    return config


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    Recursively merge override dictionary into base dictionary.

    Args:
        base: The base dictionary to be modified in-place.
        override: The dictionary with values to override.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """
    Apply environment variable overrides to the configuration.

    Supported overrides:
    - RANDOM_SEED: Integer seed for reproducibility
    - DATA_RAW_DIR, DATA_PROCESSED_DIR, etc.: Override path constants
    """
    if "RANDOM_SEED" in os.environ:
        try:
            config["random_seed"] = int(os.environ["RANDOM_SEED"])
            logger.info(f"Overriding random seed from environment: {config['random_seed']}")
        except ValueError:
            logger.warning(f"Invalid RANDOM_SEED in environment, ignoring.")

    # Path overrides
    path_mapping = {
        "DATA_RAW_DIR": "paths.data_raw",
        "DATA_PROCESSED_DIR": "paths.data_processed",
        "OUTPUTS_REPORTS_DIR": "paths.outputs_reports",
        "OUTPUTS_FIGURES_DIR": "paths.outputs_figures",
        "STATE_DIR": "paths.state",
        "CODE_DIR": "paths.code"
    }

    for env_var, config_path in path_mapping.items():
        if env_var in os.environ:
            parts = config_path.split(".")
            target = config
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = os.environ[env_var]
            logger.info(f"Overriding {parts[-1]} from environment: {os.environ[env_var]}")


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the configuration for required fields and valid ranges.

    Args:
        config: The configuration dictionary to validate.

    Raises:
        ConfigurationError: If validation fails.
    """
    # Validate random seed
    if not isinstance(config.get("random_seed"), int):
        raise ConfigurationError("random_seed must be an integer")
    if config["random_seed"] < 0:
        raise ConfigurationError("random_seed must be non-negative")

    # Validate model parameters
    model_config = config.get("model", {})
    if model_config.get("n_folds", 0) < 2:
        raise ConfigurationError("model.n_folds must be at least 2")
    if model_config.get("n_estimators_rf", 0) < 1:
        raise ConfigurationError("model.n_estimators_rf must be at least 1")
    if model_config.get("alpha_lasso", 0) < 0:
        raise ConfigurationError("model.alpha_lasso must be non-negative")

    # Validate analysis parameters
    analysis_config = config.get("analysis", {})
    if analysis_config.get("permutation_iterations", 0) < 1000:
        raise ConfigurationError("analysis.permutation_iterations must be at least 1000")

    # Validate data parameters
    data_config = config.get("data", {})
    if data_config.get("retry_attempts", 0) < 1:
        raise ConfigurationError("data.retry_attempts must be at least 1")

    # Validate validation thresholds
    val_config = config.get("validation", {})
    if val_config.get("entropy_floor", 0) <= 0:
        raise ConfigurationError("validation.entropy_floor must be positive")
    if val_config.get("mcc_min", 0) >= val_config.get("mcc_max", 0):
        raise ConfigurationError("validation.mcc_min must be less than mcc_max")


def get_random_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the random seed from configuration.

    Args:
        config: Optional config dictionary. If None, loads default config.

    Returns:
        The random seed integer.
    """
    if config is None:
        config = load_config()
    return config["random_seed"]


def set_random_seeds(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Set random seeds for reproducibility across all relevant libraries.

    Args:
        config: Optional config dictionary. If None, loads default config.
    """
    if config is None:
        config = load_config()

    seed = config["random_seed"]
    random.seed(seed)

    # Set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
        logger.debug(f"Set numpy random seed to {seed}")
    except ImportError:
        logger.debug("numpy not available, skipping numpy seed")

    # Set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        logger.debug(f"Set torch random seed to {seed}")
    except ImportError:
        logger.debug("torch not available, skipping torch seed")

    # Set tensorflow seed if available
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        logger.debug(f"Set tensorflow random seed to {seed}")
    except ImportError:
        logger.debug("tensorflow not available, skipping tensorflow seed")

    # Set sklearn seed
    try:
        import sklearn
        # sklearn doesn't have a global seed, but individual estimators accept random_state
        logger.debug("sklearn random_state handled per-estimator")
    except ImportError:
        logger.debug("sklearn not available")


def get_path(config: Dict[str, Any], path_key: str, create: bool = False) -> Path:
    """
    Get a project path from configuration.

    Args:
        config: The configuration dictionary.
        path_key: The key in config.paths to retrieve (e.g., 'data_raw').
        create: If True, create the directory if it doesn't exist.

    Returns:
        A pathlib.Path object pointing to the directory.

    Raises:
        ConfigurationError: If the path key is not found.
    """
    paths = config.get("paths", {})
    if path_key not in paths:
        raise ConfigurationError(f"Path key '{path_key}' not found in configuration")

    relative_path = paths[path_key]
    full_path = PROJECT_ROOT / relative_path

    if create:
        full_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {full_path}")

    return full_path


def get_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Get all configured paths as Path objects.

    Args:
        config: The configuration dictionary.

    Returns:
        Dictionary mapping path keys to Path objects.
    """
    paths_config = config.get("paths", {})
    return {key: get_path(config, key) for key in paths_config}


def save_config(config: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Save the current configuration to a YAML file.

    Args:
        config: The configuration dictionary to save.
        path: Optional path to save to. If None, uses CONFIG_FILE_PATH.

    Raises:
        ConfigurationError: If the file cannot be written.
    """
    save_path = path or CONFIG_FILE_PATH
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved configuration to {save_path}")
    except Exception as e:
        raise ConfigurationError(f"Failed to save configuration to {save_path}: {e}")


def initialize_default_config() -> Path:
    """
    Initialize the default configuration file if it doesn't exist.

    Returns:
        Path to the created configuration file.
    """
    if not CONFIG_FILE_PATH.exists():
        save_config(DEFAULT_CONFIG, CONFIG_FILE_PATH)
        logger.info(f"Initialized default configuration at {CONFIG_FILE_PATH}")
    else:
        logger.info(f"Configuration file already exists at {CONFIG_FILE_PATH}")
    return CONFIG_FILE_PATH


# Convenience function to get a singleton config instance
_global_config: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Get the global configuration instance.

    Returns:
        The configuration dictionary.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def reset_config() -> None:
    """Reset the global configuration to force reload."""
    global _global_config
    _global_config = None
    logger.debug("Global configuration reset")


if __name__ == "__main__":
    # Initialize default config if running as script
    config_path = initialize_default_config()
    config = load_config(config_path)

    # Set random seeds
    set_random_seeds(config)

    # Get paths
    paths = get_paths(config)

    # Log configuration summary
    logger.info("=== Configuration Summary ===")
    logger.info(f"Random Seed: {config['random_seed']}")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    for key, path in paths.items():
        logger.info(f"{key}: {path}")
    logger.info("=============================")