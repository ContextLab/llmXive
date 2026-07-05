"""
Configuration loader and validator for the llmXive project.
Validates config.yaml against a required schema and provides typed access.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# Define the expected schema structure based on project requirements
# Derived from T004 (config.yaml creation) and T005/T004b (reproducibility/logging needs)
REQUIRED_SCHEMA = {
    "global": {
        "seed": int,
        "topology_target": str,
        "simulation_params": dict
    },
    "generators": {
        "erdos_renyi": dict,
        "watts_strogatz": dict,
        "barabasi_albert": dict
    },
    "simulation": {
        "ising": dict,
        "max_steps": int,
        "temperature": float
    },
    "analysis": {
        "methods": list,
        "correction": str
    },
    "paths": {
        "data_raw": str,
        "data_analysis": str,
        "figures": str
    }
}

DEFAULT_CONFIG = {
    "global": {
        "seed": 42,
        "topology_target": "all",
        "simulation_params": {}
    },
    "generators": {
        "erdos_renyi": {"n": 100, "p": 0.1},
        "watts_strogatz": {"n": 100, "k": 4, "p": 0.1},
        "barabasi_albert": {"n": 100, "m": 2}
    },
    "simulation": {
        "ising": {"h": 0.0, "J": 1.0},
        "max_steps": 1000,
        "temperature": 1.0
    },
    "analysis": {
        "methods": ["regression", "anova"],
        "correction": "bonferroni"
    },
    "paths": {
        "data_raw": "data/raw",
        "data_analysis": "data/analysis",
        "figures": "figures"
    }
}

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load and validate the configuration file.
    
    Args:
        config_path: Path to config.yaml. Defaults to 'code/config.yaml' relative to project root.
        
    Returns:
        Validated configuration dictionary.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If config file fails schema validation.
        yaml.YAMLError: If config file is not valid YAML.
    """
    if config_path is None:
        # Default to code/config.yaml relative to the script's location or project root
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML in {config_path}: {e}")

    if config is None:
        config = {}

    # Merge with defaults to ensure all keys exist
    merged_config = _deep_merge(DEFAULT_CONFIG, config)

    # Validate against schema
    _validate_schema(merged_config)

    return merged_config

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge override dict into base dict.
    Values from override take precedence.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def _validate_schema(config: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary against the required schema.
    
    Args:
        config: Configuration dictionary to validate.
        
    Raises:
        ValueError: If validation fails.
    """
    errors = []
    
    def check_section(section: Dict[str, Any], schema: Dict[str, Any], path: str = ""):
        for key, expected_type in schema.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in section:
                errors.append(f"Missing required key: {current_path}")
                continue
            
            value = section[key]
            
            if isinstance(expected_type, dict):
                if not isinstance(value, dict):
                    errors.append(f"Expected dict for {current_path}, got {type(value).__name__}")
                else:
                    check_section(value, expected_type, current_path)
            elif isinstance(expected_type, list):
                if not isinstance(value, list):
                    errors.append(f"Expected list for {current_path}, got {type(value).__name__}")
            else:
                if not isinstance(value, expected_type):
                    errors.append(f"Expected {expected_type.__name__} for {current_path}, got {type(value).__name__}")
    
    check_section(config, REQUIRED_SCHEMA)
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ValueError(error_msg)

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely retrieve a nested value from config using dot notation.
    
    Args:
        config: Configuration dictionary.
        key_path: Dot-separated path to the value (e.g., "global.seed").
        default: Default value if key is not found.
        
    Returns:
        The value at the path, or default if not found.
    """
    keys = key_path.split('.')
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def ensure_paths_exist(config: Dict[str, Any]) -> None:
    """
    Ensure all data directories specified in config exist.
    
    Args:
        config: Validated configuration dictionary.
    """
    paths = get_config_value(config, "paths", {})
    for dir_name, dir_path in paths.items():
        if isinstance(dir_path, str):
            full_path = Path(dir_path)
            full_path.mkdir(parents=True, exist_ok=True)