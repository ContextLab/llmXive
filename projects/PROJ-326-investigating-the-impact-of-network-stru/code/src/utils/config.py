"""
Configuration management module for llmXive project.

Provides functionality to load, validate, and access configuration data
from the project's config.yaml file.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from code.src.utils.logging import log_metric, log_run
from code.src.utils.reproducibility import ensure_data_directory

# Define the required schema structure for config.yaml
REQUIRED_SCHEMA = {
    "global": {
        "random_seed": int,
        "topology_targets": list,
        "simulation_params": dict
    },
    "simulation": {
        "num_steps": int,
        "temperature": float,
        "coupling_strength": float,
        "initial_energy": float
    },
    "analysis": {
        "clustering_thresholds": list,
        "regression_models": list,
        "anova_correction_methods": list
    },
    "paths": {
        "raw_data_dir": str,
        "analysis_dir": str,
        "figures_dir": str,
        "metadata_dir": str
    }
}

DEFAULT_CONFIG = {
    "global": {
        "random_seed": 42,
        "topology_targets": ["erdos_renyi", "watts_strogatz", "barabasi_albert"],
        "simulation_params": {
            "num_nodes": 100,
            "edge_probability": 0.1,
            "rewiring_probability": 0.1,
            "m_parameter": 2
        }
    },
    "simulation": {
        "num_steps": 50,
        "temperature": 1.0,
        "coupling_strength": 1.0,
        "initial_energy": 0.0
    },
    "analysis": {
        "clustering_thresholds": [0.1, 0.2, 0.3, 0.4, 0.5],
        "regression_models": ["linear", "polynomial", "robust"],
        "anova_correction_methods": ["bonferroni", "benjamini_hochberg"]
    },
    "paths": {
        "raw_data_dir": "data/raw",
        "analysis_dir": "data/analysis",
        "figures_dir": "figures",
        "metadata_dir": "data/metadata"
    }
}

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def _deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary with values to override/merge
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def _validate_schema(config: Dict, schema: Dict, path: str = "") -> List[str]:
    """
    Validate configuration against schema.
    
    Args:
        config: Configuration dictionary to validate
        schema: Schema dictionary defining required structure and types
        path: Current path in the config (for error messages)
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    for key, expected_type in schema.items():
        current_path = f"{path}.{key}" if path else key
        
        if key not in config:
            errors.append(f"Missing required key: {current_path}")
            continue
        
        value = config[key]
        
        if isinstance(expected_type, dict):
            if not isinstance(value, dict):
                errors.append(f"Type mismatch at {current_path}: expected dict, got {type(value).__name__}")
            else:
                errors.extend(_validate_schema(value, expected_type, current_path))
        else:
            if not isinstance(value, expected_type):
                # Allow int for float and vice versa for numeric flexibility
                if expected_type in (int, float) and isinstance(value, (int, float)):
                    pass
                else:
                    errors.append(f"Type mismatch at {current_path}: expected {expected_type.__name__}, got {type(value).__name__}")
    
    return errors

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml. If None, uses default location.
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ConfigError: If file not found or validation fails
    """
    if config_path is None:
        # Default location relative to project root
        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / "code" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}")
    except Exception as e:
        raise ConfigError(f"Error reading configuration file: {e}")
    
    # Merge with defaults
    config = _deep_merge(DEFAULT_CONFIG, user_config if user_config else {})
    
    # Validate against schema
    errors = _validate_schema(config, REQUIRED_SCHEMA)
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ConfigError(error_msg)
    
    # Log configuration load for reproducibility
    try:
        log_run(
            component="config",
            action="load",
            seed=config.get("global", {}).get("random_seed", "unknown"),
            params={"config_path": str(config_path), "topology_targets": config.get("global", {}).get("topology_targets", [])}
        )
    except Exception:
        # Non-fatal if logging fails during config load
        pass
    
    return config

def get_config_value(config: Dict, key_path: str, default: Any = None) -> Any:
    """
    Get a value from config using dot notation path.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path (e.g., "global.random_seed")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = key_path.split('.')
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current

def ensure_paths_exist(config: Dict) -> None:
    """
    Ensure all directories specified in config paths exist.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ConfigError: If paths cannot be created
    """
    paths_config = config.get("paths", {})
    
    for path_name, path_value in paths_config.items():
        # Resolve relative to project root
        project_root = Path(__file__).resolve().parents[2]
        full_path = project_root / path_value
        
        try:
            ensure_data_directory(full_path)
        except Exception as e:
            raise ConfigError(f"Failed to create directory {path_name} ({full_path}): {e}")

def validate_config_file(config_path: Union[str, Path]) -> bool:
    """
    Validate a config file without loading it into memory.
    
    Args:
        config_path: Path to config file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        load_config(config_path)
        return True
    except ConfigError:
        return False