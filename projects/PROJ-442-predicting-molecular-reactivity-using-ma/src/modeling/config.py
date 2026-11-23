import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Import the logger setup utility defined in the project
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default path relative to project root
DEFAULT_CONFIG_PATH = Path("src/modeling/config.yaml")


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the environment configuration from a YAML file.

    This function implements the environment configuration management
    required by task T008. It reads the `config.yaml` file, validates
    its existence, and returns the parsed dictionary.

    Args:
        config_path (Path, optional): Path to the config file. Defaults to
            `src/modeling/config.yaml`.

    Returns:
        Dict[str, Any]: The configuration dictionary containing all settings
            (e.g., reaction_templates, model_params, data_paths).

    Raises:
        FileNotFoundError: If the config file does not exist at the specified path.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    # Resolve to absolute path relative to current working directory
    # to ensure robustness regardless of where the script is invoked from.
    abs_path = Path(os.getcwd()) / config_path

    if not abs_path.exists():
        error_msg = f"Configuration file not found: {abs_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"Loading configuration from: {abs_path}")

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            logger.warning("Configuration file is empty. Returning empty dict.")
            return {}
        
        if not isinstance(config, dict):
            error_msg = f"Configuration file must contain a top-level mapping. Found: {type(config)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Configuration loaded successfully.")
        return config

    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}")
        raise
