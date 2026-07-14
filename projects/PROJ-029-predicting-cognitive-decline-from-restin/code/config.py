"""
Configuration management.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "random_seed": 42,
    "max_ram_gb": 7,
    "dataset_id": "ds000246",
    "dataset_version": "1.0.0",
    "n_limit": 100,
    "paths": {
        "data_raw": PROJECT_ROOT / "data" / "raw",
        "data_processed": PROJECT_ROOT / "data" / "processed",
        "data_artifacts": PROJECT_ROOT / "data" / "artifacts",
        "code": PROJECT_ROOT / "code",
    }
}

def get_config() -> Dict[str, Any]:
    return CONFIG

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path