import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import random
import numpy as np

# Project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration defaults
_CONFIG = {
    "seed": 42,
    "dataset_url": "materialsproject/mp-dft-electrolytes", # Default, may be overridden
    "debug_mode": False,
    "log_level": "INFO"
}

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_config() -> Dict[str, Any]:
    return _CONFIG.copy()

def get_seed() -> int:
    return _CONFIG["seed"]

def set_seed(seed: int) -> None:
    _CONFIG["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)

def get_dataset_url() -> str:
    return _CONFIG["dataset_url"]

def set_dataset_url(url: str) -> None:
    _CONFIG["dataset_url"] = url

def get_data_dir() -> Path:
    return _PROJECT_ROOT / "data"

def get_raw_dir() -> Path:
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    return get_data_dir() / "processed"

def get_validation_dir() -> Path:
    return get_data_dir() / "validation"

def get_output_dir() -> Path:
    return get_data_dir() / "output"

def get_fallback_path() -> Path:
    return get_raw_dir() / "mock_electrolytes.csv"

def is_debug_mode() -> bool:
    return _CONFIG["debug_mode"]

def set_debug_mode(debug: bool) -> None:
    _CONFIG["debug_mode"] = debug

def get_log_level() -> str:
    return _CONFIG["log_level"]

def save_config_to_env(path: Optional[str] = None) -> None:
    if path is None:
        path = str(get_project_root() / ".env_config.json")
    with open(path, 'w') as f:
        json.dump(_CONFIG, f, indent=2)

def load_config_from_env(path: Optional[str] = None) -> None:
    if path is None:
        path = str(get_project_root() / ".env_config.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            loaded = json.load(f)
            _CONFIG.update(loaded)

def get_config_summary() -> Dict[str, Any]:
    return {
        "seed": get_seed(),
        "dataset_url": get_dataset_url(),
        "debug_mode": is_debug_mode(),
        "log_level": get_log_level(),
        "paths": {
            "project_root": str(get_project_root()),
            "data_dir": str(get_data_dir()),
            "raw_dir": str(get_raw_dir()),
            "processed_dir": str(get_processed_dir()),
            "validation_dir": str(get_validation_dir())
        }
    }
