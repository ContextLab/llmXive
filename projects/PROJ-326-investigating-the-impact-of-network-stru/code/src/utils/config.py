"""
Configuration management for the Network Topology Energy Transfer project.

This module provides a base configuration loader that validates config.yaml
against a required schema, merges with defaults, and ensures all paths exist.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from code.src.utils.logging import log_metric, log_run


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


# Define the required schema structure and default values
DEFAULT_CONFIG: Dict[str, Any] = {
    "global": {
        "random_seed": 42,
        "timeout_seconds": 300,
        "max_retries": 10,
        "log_level": "INFO"
    },
    "topology": {
        "target_graphs": 100,
        "erdos_renyi": {
            "n": 50,
            "p": 0.1,
            "clustering_target": 0.1
        },
        "watts_strogatz": {
            "n": 50,
            "k": 4,
            "beta": 0.1,
            "clustering_target": 0.3
        },
        "barabasi_albert": {
            "n": 50,
            "m": 2,
            "clustering_target": 0.1
        }
    },
    "simulation": {
        "ising": {
            "beta": 1.0,
            "steps": 100,
            "initial_state": "random",
            "temperature": 1.0
        },
        "diffusion": {
            "measure_interval": 10,
            "stability_threshold": 1e-6
        }
    },
    "analysis": {
        "regression": {
            "polynomial_degree": 2,
            "robust": True
        },
        "anova": {
            "correction_method": "bonferroni",
            "alpha": 0.05
        },
        "sensitivity": {
            "thresholds": [0.1, 0.2, 0.3, 0.4, 0.5],
            "min_thresholds": 5
        },
        "plotting": {
            "dpi": 300,
            "format": "png"
        }
    },
    "paths": {
        "data_raw": "data/raw",
        "data_analysis": "data/analysis",
        "data_metadata": "data/metadata",
        "figures": "figures",
        "paper": "paper"
    }
}


REQUIRED_KEYS: List[str] = [
    "global",
    "topology",
    "simulation",
    "analysis",
    "paths"
]

REQUIRED_GLOBAL_KEYS: List[str] = ["random_seed", "timeout_seconds", "max_retries", "log_level"]
REQUIRED_TOPOLOGY_KEYS: List[str] = ["target_graphs", "erdos_renyi", "watts_strogatz", "barabasi_albert"]
REQUIRED_SIMULATION_KEYS: List[str] = ["ising", "diffusion"]
REQUIRED_ANALYSIS_KEYS: List[str] = ["regression", "anova", "sensitivity", "plotting"]
REQUIRED_PATHS_KEYS: List[str] = ["data_raw", "data_analysis", "data_metadata", "figures", "paper"]


def _validate_schema(config: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary against the required schema.
    Raises ConfigError if validation fails.
    """
    missing_top_level = [key for key in REQUIRED_KEYS if key not in config]
    if missing_top_level:
        raise ConfigError(f"Missing required top-level keys: {missing_top_level}")

    # Validate global section
    if "global" in config:
        missing_global = [key for key in REQUIRED_GLOBAL_KEYS if key not in config["global"]]
        if missing_global:
            raise ConfigError(f"Missing required keys in 'global' section: {missing_global}")

        # Validate types
        if not isinstance(config["global"].get("random_seed"), int):
            raise ConfigError("global.random_seed must be an integer")
        if not isinstance(config["global"].get("timeout_seconds"), (int, float)):
            raise ConfigError("global.timeout_seconds must be a number")
        if not isinstance(config["global"].get("max_retries"), int):
            raise ConfigError("global.max_retries must be an integer")

    # Validate topology section
    if "topology" in config:
        missing_topo = [key for key in REQUIRED_TOPOLOGY_KEYS if key not in config["topology"]]
        if missing_topo:
            raise ConfigError(f"Missing required keys in 'topology' section: {missing_topo}")

        # Validate sub-configurations
        for topo_type in ["erdos_renyi", "watts_strogatz", "barabasi_albert"]:
            if topo_type in config["topology"]:
                sub_config = config["topology"][topo_type]
                if "n" not in sub_config or "clustering_target" not in sub_config:
                    raise ConfigError(f"Missing 'n' or 'clustering_target' in topology.{topo_type}")

    # Validate simulation section
    if "simulation" in config:
        missing_sim = [key for key in REQUIRED_SIMULATION_KEYS if key not in config["simulation"]]
        if missing_sim:
            raise ConfigError(f"Missing required keys in 'simulation' section: {missing_sim}")

        if "ising" in config["simulation"]:
            if "beta" not in config["simulation"]["ising"]:
                raise ConfigError("Missing 'beta' in simulation.ising")

        if "diffusion" in config["simulation"]:
            if "measure_interval" not in config["simulation"]["diffusion"]:
                raise ConfigError("Missing 'measure_interval' in simulation.diffusion")

    # Validate analysis section
    if "analysis" in config:
        missing_anal = [key for key in REQUIRED_ANALYSIS_KEYS if key not in config["analysis"]]
        if missing_anal:
            raise ConfigError(f"Missing required keys in 'analysis' section: {missing_anal}")

        if "sensitivity" in config["analysis"]:
            thresholds = config["analysis"]["sensitivity"].get("thresholds", [])
            if not isinstance(thresholds, list) or len(thresholds) < 1:
                raise ConfigError("analysis.sensitivity.thresholds must be a non-empty list")

    # Validate paths section
    if "paths" in config:
        missing_paths = [key for key in REQUIRED_PATHS_KEYS if key not in config["paths"]]
        if missing_paths:
            raise ConfigError(f"Missing required keys in 'paths' section: {missing_paths}")


def _merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge user configuration with defaults.
    User values take precedence over defaults.
    """
    result = default.copy()
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file, merge with defaults, and validate.

    Args:
        config_path: Path to the config.yaml file. If None, defaults to 'code/config.yaml'.

    Returns:
        Merged and validated configuration dictionary.

    Raises:
        ConfigError: If the config file is invalid or missing required keys.
        FileNotFoundError: If the config file does not exist.
    """
    if config_path is None:
        config_path = Path("code/config.yaml")
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        # If file doesn't exist, return defaults (but log a warning)
        log_metric("config_file_missing", str(config_path))
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML file: {e}")
    except IOError as e:
        raise ConfigError(f"Failed to read config file: {e}")

    if user_config is None:
        user_config = {}

    # Merge with defaults
    merged_config = _merge_configs(DEFAULT_CONFIG, user_config)

    # Validate against schema
    _validate_schema(merged_config)

    # Ensure paths exist
    ensure_paths_exist(merged_config)

    # Log successful load
    log_metric("config_loaded", str(config_path))
    log_metric("random_seed_used", merged_config["global"]["random_seed"])

    return merged_config


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from the config dictionary using a dot-separated key path.

    Args:
        config: The configuration dictionary.
        key_path: Dot-separated path (e.g., "global.random_seed").
        default: Default value if key is not found.

    Returns:
        The value at the key path, or default if not found.
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def ensure_paths_exist(config: Dict[str, Any]) -> None:
    """
    Ensure all paths defined in the config exist on disk.
    Creates directories if they don't exist.

    Args:
        config: The configuration dictionary.
    """
    paths_config = config.get("paths", {})
    project_root = Path(__file__).parent.parent.parent.parent

    for path_name, relative_path in paths_config.items():
        full_path = project_root / relative_path
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                log_metric("directory_created", str(full_path))
            except OSError as e:
                raise ConfigError(f"Failed to create directory {full_path}: {e}")


def validate_config_file(config_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Validate a config file without loading it into the main config.
    Useful for checking if a config file is valid before using it.

    Args:
        config_path: Path to the config.yaml file.

    Returns:
        True if valid, raises ConfigError otherwise.
    """
    try:
        load_config(config_path)
        return True
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Unexpected error during validation: {e}")


# Global config instance (lazy loaded)
_global_config: Optional[Dict[str, Any]] = None


def get_global_config() -> Dict[str, Any]:
    """
    Get the global configuration instance.
    Loads it if not already loaded.

    Returns:
        The global configuration dictionary.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config