"""
Verify that `code/config.yaml` defines the required canonical paths and that
each path points to an existing, writable directory.
"""

import os
import sys
import yaml
from pathlib import Path
from llmxive_toolkit import paths, get_logger
from utils.exceptions import ConfigurationError

log = get_logger(__name__)

def _load_yaml_config() -> dict:
    """Load the YAML configuration file located beside this script."""
    config_path = Path(__file__).with_name("config.yaml")
    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to read configuration: {e}") from e

    return cfg

def _validate_paths(cfg: dict) -> None:
    """Validate that required path keys exist and point to writable directories."""
    if "paths" not in cfg or not isinstance(cfg["paths"], dict):
        raise ConfigurationError("Missing or invalid 'paths' section in config.yaml")

    required_keys = ["code", "tests", "data_raw", "data_processed", "results"]
    for key in required_keys:
        if key not in cfg["paths"]:
            raise ConfigurationError(f"Missing required path key '{key}' in config.yaml")

        # Resolve using llmxive_toolkit.paths.path so tests can monkey‑patch it
        dir_path = paths.path(cfg["paths"][key])

        if not dir_path.is_dir():
            raise ConfigurationError(f"Path for '{key}' does not exist or is not a directory: {dir_path}")

        if not os.access(dir_path, os.W_OK):
            raise ConfigurationError(f"Directory for '{key}' is not writable: {dir_path}")

def verify_config() -> bool:
    """
    Public helper used by the unit test. Returns True if verification succeeds,
    otherwise raises ConfigurationError.
    """
    cfg = _load_yaml_config()
    _validate_paths(cfg)
    log.info("All configured paths exist and are writable.")
    return True

def main() -> None:
    """CLI entry point – exits with status 0 on success, 1 on failure."""
    try:
        verify_config()
    except ConfigurationError as e:
        log.error(str(e))
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
