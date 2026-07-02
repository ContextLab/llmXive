"""
Configuration management for the llmXive gene essentiality pipeline.

Loads organism IDs, confidence thresholds, and file paths from a YAML
configuration file (default: config.yaml in the project root).
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Default configuration file path relative to project root
DEFAULT_CONFIG_PATH = "config.yaml"

# Default values if config is missing or keys are absent
DEFAULT_ORGANISMS = [
    "6239",  # C. elegans
    "7227",  # D. melanogaster
    "8355",  # X. tropicalis
    "9606",  # H. sapiens
    "10090", # M. musculus
    "44689", # D. rerio
    "7955",  # Z. zebrafish (alternative ID)
    "548687",# S. pombe
    "4932",  # S. cerevisiae
]

DEFAULT_CONFIDENCE_THRESHOLDS = [500, 700, 900]

DEFAULT_PATHS = {
    "data_dir": "data",
    "results_dir": "results",
    "figures_dir": "figures",
    "state_dir": "state",
    "raw_data_dir": "data/raw",
    "phylogeny_dir": "data/phylogeny",
    "null_distribution_dir": "results/null_distribution",
    "rewired_graphs_dir": "results/null_distribution/rewired_graphs",
    "config_path": DEFAULT_CONFIG_PATH,
}


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file. Defaults to DEFAULT_CONFIG_PATH.

    Returns:
        Dictionary containing the merged configuration (defaults + file overrides).

    Raises:
        ConfigError: If the config file cannot be read or parsed, or if required
                     sections are missing.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    config_path = Path(config_path)

    # Start with defaults
    config: Dict[str, Any] = {
        "organisms": DEFAULT_ORGANISMS.copy(),
        "confidence_thresholds": DEFAULT_CONFIDENCE_THRESHOLDS.copy(),
        "paths": DEFAULT_PATHS.copy(),
    }

    if not config_path.exists():
        # If config file doesn't exist, return defaults but log a warning
        # In a real pipeline, we might want to generate a default config file
        # For now, we just use defaults
        return config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            file_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML config file: {e}")
    except IOError as e:
        raise ConfigError(f"Failed to read config file: {e}")

    if file_config is None:
        # Empty file, return defaults
        return config

    # Merge file config with defaults
    if "organisms" in file_config:
        if not isinstance(file_config["organisms"], list):
            raise ConfigError("'organisms' must be a list")
        config["organisms"] = file_config["organisms"]

    if "confidence_thresholds" in file_config:
        if not isinstance(file_config["confidence_thresholds"], list):
            raise ConfigError("'confidence_thresholds' must be a list")
        config["confidence_thresholds"] = file_config["confidence_thresholds"]

    if "paths" in file_config:
        if not isinstance(file_config["paths"], dict):
            raise ConfigError("'paths' must be a dictionary")
        config["paths"].update(file_config["paths"])

    return config


def get_organisms(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Get the list of organism IDs to process.

    Args:
        config: Optional config dict. If None, loads from default config file.

    Returns:
        List of organism IDs (as strings, typically taxonomic IDs).
    """
    if config is None:
        config = load_config()
    return config.get("organisms", DEFAULT_ORGANISMS)


def get_confidence_thresholds(config: Optional[Dict[str, Any]] = None) -> List[int]:
    """
    Get the list of STRING confidence thresholds to use.

    Args:
        config: Optional config dict. If None, loads from default config file.

    Returns:
        List of confidence thresholds (integers, typically 0-1000).
    """
    if config is None:
        config = load_config()
    return config.get("confidence_thresholds", DEFAULT_CONFIDENCE_THRESHOLDS)


def get_path(key: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get a specific path from the configuration.

    Args:
        key: The path key (e.g., 'data_dir', 'phylogeny_dir').
        config: Optional config dict. If None, loads from default config file.

    Returns:
        The path string for the given key.

    Raises:
        ConfigError: If the key is not found in paths.
    """
    if config is None:
        config = load_config()

    paths = config.get("paths", {})
    if key not in paths:
        raise ConfigError(f"Path key '{key}' not found in configuration")

    return paths[key]


def ensure_dirs(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensure all directories specified in the config exist.

    Args:
        config: Optional config dict. If None, loads from default config file.
    """
    if config is None:
        config = load_config()

    paths = config.get("paths", {})
    for key, path_str in paths.items():
        if key.endswith("_dir") or key.endswith("_path"):
            # Only create directories, not files
            if path_str.endswith("_path"):
                continue
            path = Path(path_str)
            path.mkdir(parents=True, exist_ok=True)


# Convenience function to get a fully resolved config with paths
def get_full_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the full configuration with resolved paths.

    Args:
        config_path: Path to the YAML config file. Defaults to DEFAULT_CONFIG_PATH.

    Returns:
        Complete configuration dictionary.
    """
    config = load_config(config_path)
    ensure_dirs(config)
    return config


if __name__ == "__main__":
    # Simple test to verify config loading works
    import json

    cfg = get_full_config()
    print("Loaded configuration:")
    print(json.dumps(cfg, indent=2, default=str))