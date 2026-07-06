"""
Configuration management for llmXive project.
Handles loading YAML configuration and merging with environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Project root is determined by the presence of the .git directory or a specific marker
# Defaulting to the parent of this file's directory structure: code/ -> project_root
# Based on the provided file structure, this file is at code/src/utils/config.py
# So project root is code/
_PROJECT_ROOT: Optional[Path] = None

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    The project root is assumed to be the parent of the 'src' directory.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        current_file_path = Path(__file__).resolve()
        # Navigate up: code/src/utils/config.py -> code/src/utils -> code/src -> code
        _PROJECT_ROOT = current_file_path.parent.parent.parent
    return _PROJECT_ROOT

def load_yaml_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Loads a YAML configuration file and returns it as a dictionary.

    Args:
        config_path: Path to the YAML configuration file. Can be relative to project root or absolute.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    path = Path(config_path)
    if not path.is_absolute():
        # Try relative to project root first, then current working directory
        full_path = get_project_root() / path
        if not full_path.exists():
            full_path = Path.cwd() / path
        path = full_path

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Handle case where YAML is empty or just comments
    if config is None:
        return {}
    
    return config

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieves an environment variable.

    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.

    Returns:
        The value of the environment variable or the default.
    """
    return os.environ.get(key, default)

def merge_env_overrides(config: Dict[str, Any], prefix: str = "LLMXIVE_") -> Dict[str, Any]:
    """
    Overrides configuration values with environment variables.
    Environment variables should be prefixed (e.g., LLMXIVE_DATA_PATH).
    Nested keys are supported using underscores (e.g., LLMXIVE_MODEL_LR).

    Args:
        config: The base configuration dictionary.
        prefix: The prefix for environment variables.

    Returns:
        A new dictionary with environment overrides applied.
    """
    import re

    def set_nested(d: Dict, keys: list, value: Any) -> None:
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                d[key] = value
            else:
                if key not in d or not isinstance(d[key], dict):
                    d[key] = {}
                d = d[key]

    def convert_value(val: str) -> Any:
        """Attempts to convert string to int, float, or bool."""
        if val.lower() == 'true':
            return True
        if val.lower() == 'false':
            return False
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val

    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase
            env_key = key[len(prefix):].lower()
            # Split by underscore to handle nested keys
            keys = env_key.split('_')
            set_nested(config, keys, convert_value(value))

    return config

def load_config(config_path: Union[str, Path], env_prefix: str = "LLMXIVE_") -> Dict[str, Any]:
    """
    Loads a YAML config and merges it with environment variable overrides.

    Args:
        config_path: Path to the YAML configuration file.
        env_prefix: Prefix for environment variables to look for overrides.

    Returns:
        Merged configuration dictionary.
    """
    config = load_yaml_config(config_path)
    return merge_env_overrides(config, env_prefix)

def get_config_value(config: Dict[str, Any], key_path: str, default: Optional[Any] = None) -> Any:
    """
    Retrieves a value from a nested configuration dictionary using a dot-separated key path.

    Args:
        config: The configuration dictionary.
        key_path: Dot-separated path to the key (e.g., "model.learning_rate").
        default: Default value if the key path is not found.

    Returns:
        The value at the key path or the default.
    """
    keys = key_path.split('.')
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """
    Saves a configuration dictionary to a YAML file.

    Args:
        config: The configuration dictionary to save.
        config_path: Path where the YAML file should be saved.
    """
    path = Path(config_path)
    if not path.is_absolute():
        path = get_project_root() / path
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)