"""
Configuration management module for the crystal structure prediction project.

Provides utilities for path handling, seed management, hyperparameter storage,
runtime configuration I/O, and a generic argument parser.

This implementation is deliberately lightweight to satisfy the needs of
the current tasks (e.g., environment validation) while remaining compatible
with the broader codebase.
"""

import os
import json
import random
import numpy as np
import argparse
from pathlib import Path
from typing import Any, Dict, Optional, Union

# llmxive toolkit provides convenient path factories that create directories as needed.
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Project root and basic path helpers
# ----------------------------------------------------------------------

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    Assumes this file lives in <project_root>/code/config.py.
    """
    return Path(__file__).resolve().parent.parent

# Helper to ensure a directory exists; returns the Path object.
def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure that the given directory exists (creates it if necessary).

    Args:
        path: Directory path as a string or Path object.

    Returns:
        Path object pointing to the ensured directory.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

# ----------------------------------------------------------------------
# Path getters delegating to llmxive_toolkit.paths
# ----------------------------------------------------------------------

def get_path_data() -> Path:
    """Path to the top-level data directory."""
    return paths.data()

def get_path_raw_data() -> Path:
    """Path to the raw data subdirectory."""
    return paths.data("raw")

def get_path_processed_data(filename: Optional[str] = None) -> Path:
    """
    Path to the processed data directory or a specific file within it.

    Args:
        filename: Optional filename to append.

    Returns:
        Path object.
    """
    base = paths.data("processed")
    return base if filename is None else base / filename

def get_path_results() -> Path:
    """Path to the results directory."""
    return paths.results()

def get_path_validation() -> Path:
    """Path to the validation directory."""
    return paths.validation()

def get_path_models() -> Path:
    """Path to the models directory."""
    return paths.models()

def get_path_logs() -> Path:
    """Path to the logs directory."""
    return paths.logs()

def get_path_figures() -> Path:
    """Path to the figures directory."""
    return paths.figures()

def get_path_code() -> Path:
    """Path to the code directory."""
    return paths.code()

def get_path_tests() -> Path:
    """Path to the tests directory."""
    return paths.tests()

def get_path_specs() -> Path:
    """Path to the specs directory."""
    return paths.specs()

# ----------------------------------------------------------------------
# Seed handling
# ----------------------------------------------------------------------

DEFAULT_SEED = 42

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set seeds for reproducibility across random, numpy, and python hash.

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

# ----------------------------------------------------------------------
# Runtime configuration (e.g., training device) handling
# ----------------------------------------------------------------------

def get_runtime_config_path() -> Path:
    """Path to the runtime configuration JSON file."""
    return get_path_results() / "runtime_config.json"

def load_runtime_config() -> Dict[str, Any]:
    """
    Load the runtime configuration from disk.

    Returns:
        Dictionary with configuration values.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    config_path = get_runtime_config_path()
    if not config_path.is_file():
        raise FileNotFoundError(f"Runtime config not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_runtime_config(config: Dict[str, Any]) -> None:
    """
    Save the provided configuration dictionary to the runtime config file.

    Args:
        config: Dictionary to serialize as JSON.
    """
    config_path = get_runtime_config_path()
    ensure_directory(config_path.parent)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

# ----------------------------------------------------------------------
# Hyperparameter storage (simple in‑memory dict)
# ----------------------------------------------------------------------

_hyperparameters: Dict[str, Any] = {}

def get_hyperparameter(name: str) -> Any:
    """Retrieve a hyperparameter value by name; returns None if unset."""
    return _hyperparameters.get(name)

def set_hyperparameter(name: str, value: Any) -> None:
    """Set or update a hyperparameter."""
    _hyperparameters[name] = value

def get_all_hyperparameters() -> Dict[str, Any]:
    """Return a copy of all stored hyperparameters."""
    return dict(_hyperparameters)

# ----------------------------------------------------------------------
# Consolidated config dictionary (paths + hyperparameters)
# ----------------------------------------------------------------------

def get_config_dict() -> Dict[str, Any]:
    """
    Returns a dictionary containing the most commonly used configuration
    values, including directory paths and any hyperparameters that have
    been set.
    """
    cfg = {
        "project_root": str(get_project_root()),
        "paths": {
            "data": str(get_path_data()),
            "raw_data": str(get_path_raw_data()),
            "processed_data": str(get_path_processed_data()),
            "results": str(get_path_results()),
            "validation": str(get_path_validation()),
            "models": str(get_path_models()),
            "logs": str(get_path_logs()),
            "figures": str(get_path_figures()),
            "code": str(get_path_code()),
            "tests": str(get_path_tests()),
            "specs": str(get_path_specs()),
        },
        "hyperparameters": get_all_hyperparameters(),
    }
    return cfg

# ----------------------------------------------------------------------
# Argument parser utility
# ----------------------------------------------------------------------

def create_parser() -> argparse.ArgumentParser:
    """
    Create a reusable ArgumentParser with common project-wide options.

    Currently supports:
    - --seed : set the random seed
    - --config : path to a JSON config file to load (optional)
    """
    parser = argparse.ArgumentParser(description="Project configuration parser")
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a JSON configuration file to load and merge",
    )
    return parser

def main() -> int:
    """
    Simple CLI entry point that parses common arguments, sets the seed,
    and optionally merges a JSON config file into the in‑memory hyperparameter store.

    Returns:
        Exit code (0 on success, 1 on error).
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        set_seed(args.seed)
        if args.config:
            cfg_path = Path(args.config)
            if not cfg_path.is_file():
                raise FileNotFoundError(f"Config file not found: {cfg_path}")
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
            # Merge top‑level keys into hyperparameters
            if isinstance(cfg_data, dict):
                for k, v in cfg_data.items():
                    set_hyperparameter(k, v)
        # Optionally, write an initial runtime config with the seed info
        runtime_cfg = {"seed": args.seed, "hyperparameters_loaded": bool(args.config)}
        save_runtime_config(runtime_cfg)
        return 0
    except Exception as e:
        print(f"Error in config CLI: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    raise SystemExit(exit_code)
