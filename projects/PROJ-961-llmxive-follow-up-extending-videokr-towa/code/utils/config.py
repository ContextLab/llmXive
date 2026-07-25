"""Configuration management for llmXive project."""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_path(relative_path: str) -> Path:
    """Return a path relative to the project root."""
    return get_project_root() / relative_path

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = Path(path) if isinstance(path, str) else path
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)

def get_config() -> Dict[str, Any]:
    """Load configuration from config file if exists."""
    config_path = get_path("config.json")
    if config_path.exists():
        import json
        with open(config_path, "r") as f:
            return json.load(f)
    return {}
