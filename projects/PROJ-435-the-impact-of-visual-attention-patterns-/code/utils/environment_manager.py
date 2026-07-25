"""
Environment Manager for Reproducibility and Configuration

This module provides utilities for:
- Loading configuration from code/config.yaml
- Setting random seeds for reproducibility (Python, NumPy)
- Managing file paths relative to project root
- Setting up logging infrastructure
"""

import os
import random
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file. If None, defaults to 'code/config.yaml'
                     relative to the project root.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    if config_path is None:
        # Default to code/config.yaml relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "code" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries, with 'override' taking precedence.

    Args:
        base: The base dictionary.
        override: The dictionary with values to override.

    Returns:
        A new merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def setup_reproducibility(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Set random seeds for reproducibility based on configuration.

    This function sets seeds for:
    - Python's random module
    - NumPy's random number generator

    Args:
        config: Configuration dictionary. If None, loads from default config file.
    """
    if config is None:
        config = load_config()

    seeds = config.get('random_seeds', {})
    python_seed = seeds.get('python', 42)
    numpy_seed = seeds.get('numpy', 42)

    # Set Python random seed
    random.seed(python_seed)

    # Set NumPy random seed
    try:
        import numpy as np
        np.random.seed(numpy_seed)
    except ImportError:
        pass  # NumPy might not be installed, but that's okay

    logging.info(f"Reproducibility setup: Python seed={python_seed}, NumPy seed={numpy_seed}")


def get_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
    """
    Get standardized paths for project directories.

    Args:
        config: Configuration dictionary. If None, loads from default config file.

    Returns:
        Dictionary mapping path keys (e.g., 'raw_data', 'derived_data') to Path objects.
    """
    if config is None:
        config = load_config()

    project_root = Path(__file__).resolve().parent.parent.parent
    path_configs = config.get('paths', {})

    paths = {}
    for key, relative_path in path_configs.items():
        paths[key] = project_root / relative_path

    return paths


def get_config_value(key: str, default: Any = None, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Get a value from the configuration using dot-notation key.

    Args:
        key: Dot-notation key (e.g., 'random_seeds.python', 'analysis.ivt_duration_threshold').
        default: Default value if the key is not found.
        config: Configuration dictionary. If None, loads from default config file.

    Returns:
        The configuration value or the default.
    """
    if config is None:
        config = load_config()

    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value


def setup_logging(config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Set up logging infrastructure based on configuration.

    Args:
        config: Configuration dictionary. If None, loads from default config file.

    Returns:
        The root logger configured according to the specification.
    """
    if config is None:
        config = load_config()

    log_config = config.get('logging', {})
    level_str = log_config.get('level', 'INFO')
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file', 'state/pipeline.log')

    # Ensure log directory exists
    project_root = Path(__file__).resolve().parent.parent.parent
    log_path = project_root / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level_str.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging infrastructure initialized.")
    return logger


def main():
    """
    Main function to demonstrate environment manager functionality.
    """
    # Load configuration
    config = load_config()

    # Set up reproducibility
    setup_reproducibility(config)

    # Get paths
    paths = get_paths(config)
    print("Project Paths:")
    for key, path in paths.items():
        print(f"  {key}: {path}")

    # Get specific config values
    print("\nConfiguration Values:")
    print(f"  Python Seed: {get_config_value('random_seeds.python', config=config)}")
    print(f"  IVT Duration Threshold: {get_config_value('analysis.ivt_duration_threshold', config=config)}")
    print(f"  Max Data Loss Percent: {get_config_value('analysis.max_data_loss_percent', config=config)}")

    # Setup logging
    logger = setup_logging(config)
    logger.info("Environment manager demonstration complete.")


if __name__ == "__main__":
    main()
