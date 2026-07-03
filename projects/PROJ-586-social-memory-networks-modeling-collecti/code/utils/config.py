"""Environment management and configuration."""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG = {
    "seed": 42,
    "device": "cpu",
    "model": "opt-125m",
    "precision": "float32"
}

def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return DEFAULT_CONFIG
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_config() -> Dict[str, Any]:
    config_path = Path("code/config.yaml")
    return load_config(config_path)
