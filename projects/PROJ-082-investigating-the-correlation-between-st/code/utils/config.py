import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
import yaml

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parents[2]

def set_seed(seed: int):
    """Set the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_project_root() / "code" / "config" / "config.yaml"

def get_output_path() -> Path:
    """Get the path to the output directory."""
    return get_project_root() / "data" / "processed"

def get_figure_path() -> Path:
    """Get the path to the figures directory."""
    return get_project_root() / "data" / "derived"

def load_config() -> Dict[str, Any]:
    """
    Load the configuration from the config file.
    If the file doesn't exist, return default values.
    """
    config_path = get_config_path()
    default_config = {
        "seed": 42,
        "paths": {
            "raw_data": "data/raw",
            "processed_data": "data/processed",
            "derived_data": "data/derived",
            "figures": "data/derived"
        },
        "limits": {
            "max_memory_mb": 6000,
            "max_plot_size_mb": 5
        }
    }
    
    if not config_path.exists():
        return default_config
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            # Merge with defaults
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    except Exception as e:
        print(f"Warning: Could not load config file: {e}. Using defaults.")
        return default_config

def load_config_from_env() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    """
    config = load_config()
    if "PROJECT_SEED" in os.environ:
        config["seed"] = int(os.environ["PROJECT_SEED"])
    return config

def resolve_path(path_str: str, base: Optional[Path] = None) -> Path:
    """Resolve a path string to a Path object."""
    if base is None:
        base = get_project_root()
    return base / path_str

def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def get_seed() -> int:
    """Get the random seed from the config."""
    config = load_config()
    return config.get("seed", 42)

def update_config(key: str, value: Any):
    """Update a value in the config file."""
    config_path = get_config_path()
    config = load_config()
    config[key] = value
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a value from the config."""
    config = load_config()
    return config.get(key, default)

def save_config(config: Dict[str, Any]):
    """Save the config to the config file."""
    config_path = get_config_path()
    ensure_directory(config_path.parent)
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

def main():
    """
    Entry point for script execution.
    """
    config = load_config()
    print(f"Loaded config: {config}")
    print(f"Project root: {get_project_root()}")
    print(f"Output path: {get_output_path()}")

if __name__ == "__main__":
    main()