import os
import sys
import logging
import logging.config
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def get_project_root() -> Path:
    """Return the project root directory (parent of 'code')."""
    current_file = Path(__file__).resolve()
    # Assume structure: code/utils/logging_init.py -> root is 2 levels up
    return current_file.parent.parent.parent

def load_logging_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load logging configuration from a YAML file.
    
    Args:
        config_path: Path to the logging config YAML. Defaults to 
                     code/config/logging_config.yaml.
                     
    Returns:
        Dictionary containing the logging configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    if config_path is None:
        root = get_project_root()
        config_path = root / "code" / "config" / "logging_config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Logging config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    # Ensure paths in config are absolute or resolved relative to project root
    if 'handlers' in config:
        for handler_name, handler_config in config['handlers'].items():
            if isinstance(handler_config, dict) and 'filename' in handler_config:
                filename = handler_config['filename']
                if not os.path.isabs(filename):
                    # Resolve relative to project root
                    handler_config['filename'] = str(get_project_root() / filename)
                    
    return config

def setup_global_logger() -> logging.Logger:
    """
    Initialize the global logging system based on code/config/logging_config.yaml.
    
    This function loads the configuration, applies it to the root logger,
    and returns the configured logger instance.
    
    Returns:
        The root logger instance, now configured.
        
    Raises:
        FileNotFoundError: If logging_config.yaml is missing.
        KeyError: If required sections are missing from the config.
        ValueError: If the configuration is invalid.
    """
    config = load_logging_config()
    
    # Apply configuration to the root logger
    # This configures all handlers, formatters, and loggers defined in the file
    logging.config.dictConfig(config)
    
    # Return the root logger (or a specific named logger if preferred)
    return logging.getLogger()

def main() -> None:
    """
    Entry point for testing the logging initialization.
    Demonstrates that the logger is correctly configured.
    """
    try:
        logger = setup_global_logger()
        logger.info("Logging system initialized successfully.")
        logger.debug("Debug message to verify debug level is active.")
        logger.warning("This is a test warning message.")
        logger.error("This is a test error message.")
        print(f"Logger name: {logger.name}")
        print(f"Logger level: {logging.getLevelName(logger.level)}")
    except Exception as e:
        print(f"Failed to initialize logging: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()