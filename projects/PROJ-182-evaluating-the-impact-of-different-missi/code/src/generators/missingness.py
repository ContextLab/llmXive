"""
Configuration loader for simulation parameters.
Reads YAML configuration files for simulation, missingness, and estimation settings.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

from src.logging_config import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path("config")


def load_yaml_config(filename: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file from the config directory.

    Args:
        filename: Name of the YAML file (e.g., 'simulation.yaml').

    Returns:
        Dictionary containing the configuration.
    """
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")

    with open(filepath, 'r') as f:
        config = yaml.safe_load(f)

    logger.debug(f"Loaded configuration from {filepath}")
    return config


def load_simulation_config() -> Dict[str, Any]:
    """Load simulation configuration (sample_size, true_effect, seed, etc.)."""
    return load_yaml_config("simulation.yaml")


def load_missingness_config() -> Dict[str, Any]:
    """Load missingness configuration (rates, mechanisms)."""
    return load_yaml_config("missingness.yaml")


def load_estimation_config() -> Dict[str, Any]:
    """Load estimation configuration (bandwidth_rule, imputation_count, etc.)."""
    return load_yaml_config("estimation.yaml")


def get_missingness_rate(mechanism: str, config: Optional[Dict[str, Any]] = None) -> float:
    """
    Retrieve the missingness rate for a specific mechanism from config.

    Args:
        mechanism: The mechanism name (e.g., 'MCAR').
        config: Optional pre-loaded config. If None, loads from file.

    Returns:
        float: The missingness rate.
    """
    if config is None:
        config = load_missingness_config()

    rates = config.get("rates", {})
    if mechanism.upper() not in rates:
        raise ValueError(f"Missing rate for mechanism '{mechanism}' not found in config.")

    return float(rates[mechanism.upper()])