"""
Configuration loader for the llmXive research pipeline.

Handles project paths, random seeds, and environment-based overrides.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Base directory relative to the project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default configuration values
DEFAULTS: Dict[str, Any] = {
    "seed": 42,
    "data_raw_dir": "data/raw",
    "data_processed_dir": "data/processed",
    "data_contracts_dir": "data/contracts",
    "data_analysis_dir": "data/analysis",
    "prompts_dir": "prompts",
    "logs_dir": "logs",
    "figures_dir": "figures",
    "models_cache_dir": "models_cache",
    "timeout_seconds": 300,
    "max_retries": 3,
    "batch_size": 16,
    "temperature": 0.0,
    "top_p": 1.0,
    "do_sample": False,
}

def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    return _PROJECT_ROOT

def get_config_path(config_file: str = "config.yaml") -> Path:
    """Returns the path to the configuration file."""
    return get_project_root() / config_file

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file, merging with defaults and environment overrides.

    Args:
        config_file: Optional path to the config file relative to project root.
                    If None, defaults to 'config.yaml'.

    Returns:
        A dictionary containing the merged configuration.
    """
    cfg_path = get_config_path(config_file) if config_file else get_config_path()
    config = DEFAULTS.copy()

    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            file_config = yaml.safe_load(f) or {}
            config.update(file_config)

    # Environment variable overrides (prefix: LLMXIVE_)
    for key in config:
        env_key = f"LLMXIVE_{key.upper()}"
        if env_key in os.environ:
            val = os.environ[env_key]
            # Attempt to cast to the type of the default value
            default_val = DEFAULTS.get(key)
            if isinstance(default_val, bool):
                config[key] = val.lower() in ("true", "1", "yes")
            elif isinstance(default_val, int):
                try:
                    config[key] = int(val)
                except ValueError:
                    pass
            elif isinstance(default_val, float):
                try:
                    config[key] = float(val)
                except ValueError:
                    pass
            else:
                config[key] = val

    return config

def resolve_path(config: Dict[str, Any], key: str, create: bool = False) -> Path:
    """
    Resolves a configuration path string to an absolute Path object.

    Args:
        config: The configuration dictionary.
        key: The key in the config dictionary containing the relative path.
        create: If True, creates the directory if it doesn't exist.

    Returns:
        Absolute Path object.
    """
    if key not in config:
        raise KeyError(f"Configuration key '{key}' not found.")

    relative_path = config[key]
    if not relative_path:
        return get_project_root()

    abs_path = get_project_root() / relative_path

    if create and not abs_path.exists():
        abs_path.mkdir(parents=True, exist_ok=True)

    return abs_path

def get_seed(config: Dict[str, Any]) -> int:
    """
    Retrieves the random seed from config and sets global seeds for reproducibility.

    Args:
        config: The configuration dictionary.

    Returns:
        The integer seed value.
    """
    seed = int(config.get("seed", DEFAULTS["seed"]))
    random.seed(seed)
    # Note: torch and numpy seeds are set in their respective modules where imported
    return seed

def get_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Resolves all standard directory paths from the configuration.

    Args:
        config: The configuration dictionary.

    Returns:
        Dictionary mapping logical names to absolute Path objects.
    """
    paths = {}
    path_keys = [
        "data_raw_dir",
        "data_processed_dir",
        "data_contracts_dir",
        "data_analysis_dir",
        "prompts_dir",
        "logs_dir",
        "figures_dir",
        "models_cache_dir",
    ]

    for key in path_keys:
        paths[key] = resolve_path(config, key, create=True)

    return paths

def main():
    """
    CLI entry point to dump the current effective configuration.
    Useful for debugging environment variable overrides.
    """
    import json

    cfg = load_config()
    paths = get_paths(cfg)
    seed = get_seed(cfg)

    output = {
        "effective_config": cfg,
        "resolved_paths": {k: str(v) for k, v in paths.items()},
        "seed": seed,
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()