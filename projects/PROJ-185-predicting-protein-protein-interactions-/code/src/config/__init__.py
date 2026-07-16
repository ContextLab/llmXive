"""
Configuration package for the PPI prediction pipeline.
Provides loading utilities for species and parameters YAML files.
"""
import yaml
from pathlib import Path
from typing import Any, Dict

_CONFIG_DIR = Path(__file__).parent


def load_species_config() -> Dict[str, Any]:
    """
    Load the species configuration from species.yaml.

    Returns:
        Dict containing species definitions (e.g., arabidopsis).
    """
    config_path = _CONFIG_DIR / "species.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_parameters_config() -> Dict[str, Any]:
    """
    Load the pipeline parameters from parameters.yaml.

    Returns:
        Dict containing global pipeline parameters.
    """
    config_path = _CONFIG_DIR / "parameters.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


__all__ = ["load_species_config", "load_parameters_config"]