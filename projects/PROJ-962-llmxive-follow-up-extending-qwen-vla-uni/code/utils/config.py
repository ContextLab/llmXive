"""
Configuration management for the Non-Neural VLA Approximation pipeline.
Handles dataset paths, simulation parameters, and clustering strategy parameters.
"""
import os
import yaml
from typing import Dict, Any, Optional

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

# Default configuration values
DEFAULT_CONFIG = {
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_results": "data/results",
        "models": "artifacts/models",
        "vla_proxy_baseline": "data/results/vla_proxy_baseline.parquet"
    },
    "clustering": {
        "initial_k": 50,
        "silhouette_threshold": 0.25,
        "k_decrement_step": 5,
        "max_attempts": 10,
        "min_samples_per_cluster": 100
    },
    "simulation": {
        "joint_limits": {
            "shoulder_pan": [-6.28, 6.28],
            "shoulder_lift": [-3.14, 3.14],
            "elbow": [-3.14, 3.14],
            "wrist_1": [-6.28, 6.28],
            "wrist_2": [-6.28, 6.28],
            "wrist_3": [-6.28, 6.28]
        },
        "task_types": ["grasp", "navigate", "place"],
        "max_steps": 100,
        "collision_threshold": 0.01
    },
    "training": {
        "bert_model": "bert-base-uncased",
        "r2_threshold": 0.6,
        "train_test_split": 0.8
    },
    "evaluation": {
        "confidence_interval": 0.95,
        "fidelity_error_margin": 0.05
    }
}

def get_config_path() -> str:
    """Returns the path to the configuration file."""
    return DEFAULT_CONFIG_PATH

def load_config_from_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file.
    Falls back to DEFAULT_CONFIG if file is missing.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            # Merge with defaults to ensure all keys exist
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]
                elif isinstance(DEFAULT_CONFIG[key], dict):
                    for sub_key in DEFAULT_CONFIG[key]:
                        if sub_key not in config[key]:
                            config[key][sub_key] = DEFAULT_CONFIG[key][sub_key]
            return config
    return DEFAULT_CONFIG

def get_config() -> Dict[str, Any]:
    """Returns the merged configuration dictionary."""
    return load_config_from_file()

def set_config_value(key: str, value: Any) -> None:
    """
    Sets a specific value in the configuration.
    Note: This modifies the in-memory config. To persist, save to YAML manually.
    """
    config = get_config()
    keys = key.split('.')
    current = config
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value

def get_clustering_params() -> Dict[str, Any]:
    """Returns clustering-specific parameters."""
    return get_config().get("clustering", DEFAULT_CONFIG["clustering"])

def get_data_params() -> Dict[str, Any]:
    """Returns data path parameters."""
    return get_config().get("paths", DEFAULT_CONFIG["paths"])

def get_simulation_params() -> Dict[str, Any]:
    """Returns simulation-specific parameters."""
    return get_config().get("simulation", DEFAULT_CONFIG["simulation"])
