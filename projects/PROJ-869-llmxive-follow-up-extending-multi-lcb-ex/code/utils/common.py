"""
Common utility functions for the project.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

def ensure_dir(path: str) -> Path:
    """Ensure directory exists."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def load_json(path: str) -> Any:
    """Load JSON from file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Any, path: str):
    """Save data to JSON file."""
    dir_path = Path(path).parent
    if dir_path:
        dir_path.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_yaml(path: str) -> Any:
    """Load YAML from file."""
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        raise ImportError("PyYAML is required to load YAML files.")

def save_yaml(data: Any, path: str):
    """Save data to YAML file."""
    try:
        import yaml
        dir_path = Path(path).parent
        if dir_path:
            dir_path.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        raise ImportError("PyYAML is required to save YAML files.")
