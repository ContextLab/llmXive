"""
Configuration management module for the molecular reactivity project.
Loads and validates the config.yaml file.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Default path relative to project root
DEFAULT_CONFIG_PATH = Path("src/modeling/config.yaml")

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file. Defaults to src/modeling/config.yaml.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    # Resolve path relative to project root if not absolute
    if not config_path.is_absolute():
        # Try relative to current working directory first, then project root
        if config_path.exists():
            full_path = config_path
        else:
            # Assume project root is parent of 'src'
            project_root = Path.cwd()
            full_path = project_root / config_path
    else:
        full_path = config_path

    if not full_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {full_path}")

    logger.info(f"Loading configuration from: {full_path}")

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        raise

    # Basic validation of required sections
    required_sections = ['project', 'data', 'modeling']
    missing_sections = [sec for sec in required_sections if sec not in config]
    if missing_sections:
        logger.warning(f"Missing required configuration sections: {missing_sections}")
        # We don't raise here to allow for partial configs, but log a warning

    return config

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from the config dictionary using a dot-notation path.

    Args:
        config: The configuration dictionary.
        key_path: Dot-separated path to the value (e.g., 'modeling.training.n_estimators').
        default: Default value if the key is not found.

    Returns:
        The value at the specified path, or the default if not found.
    """
    keys = key_path.split('.')
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value

def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """
    Save configuration to a YAML file.

    Args:
        config: The configuration dictionary to save.
        config_path: Path to save the config file. Defaults to src/modeling/config.yaml.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if not config_path.parent.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Configuration saved to: {config_path}")
