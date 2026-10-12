"""
verify_config.py
-----------------
Script to verify that the project configuration file `code/config.yaml` defines the
canonical directory paths and that those directories exist and are writable.

This script is part of task **T001f**.  It is executed directly (e.g. ``python
-m code.verify_config``) and will raise an exception if any verification step
fails.  On success it prints a short confirmation message.
"""

import sys
import yaml
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_config() -> dict:
    """Load ``code/config.yaml`` as a Python dictionary."""
    config_path = Path(__file__).with_name("config.yaml")
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict) or "paths" not in cfg:
        raise ValueError("Configuration file must contain a top‑level 'paths' mapping.")
    return cfg["paths"]

def _ensure_directory(dir_path: Path) -> None:
    """Create the directory if it does not exist and verify write access."""
    dir_path.mkdir(parents=True, exist_ok=True)
    if not os.access(dir_path, os.W_OK):
        raise PermissionError(f"Directory is not writable: {dir_path}")

    # Try writing a temporary file and delete it to guarantee writability.
    test_file = dir_path / ".write_test"
    try:
        test_file.write_text("test", encoding="utf-8")
    finally:
        if test_file.exists():
            test_file.unlink()

def verify_config() -> None:
    """
    Verify that the configuration defines the required keys and that each
    corresponding directory exists and is writable.
    """
    required_keys = {"code", "tests", "data_raw", "data_processed", "results"}
    cfg_paths = _load_config()

    missing = required_keys - cfg_paths.keys()
    if missing:
        raise KeyError(f"Missing required path keys in config.yaml: {missing}")

    # Resolve each relative path against the project root using llmxive_toolkit.
    for key in required_keys:
        rel_path = cfg_paths[key]
        # Use the appropriate helper from ``paths`` to obtain a Path object.
        # ``paths`` provides a generic ``path`` method; we use it for all keys.
        dir_path = paths.path(rel_path)
        _ensure_directory(dir_path)
        log.info("Verified writable directory for %s: %s", key, dir_path)

    log.info("All configuration paths verified successfully.")

if __name__ == "__main__":
    try:
        verify_config()
    except Exception as e:
        log.error("Configuration verification failed: %s", e)
        sys.exit(1)
    else:
        print("Configuration verification passed.")
        sys.exit(0)
