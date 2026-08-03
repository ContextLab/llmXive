import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List
import numpy as np

# Configuration Constants
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Internal State
_config: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": BATCH_SIZE,
    "project_root": _PROJECT_ROOT,
    "drift_threshold": 0.5,
    "centroid_model": "all-MiniLM-L6-v2",
    "baseline_model": "google/flan-t5-small",
}

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = _config["random_seed"]
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_config() -> Dict[str, Any]:
    """Return the current configuration dictionary."""
    return _config.copy()

def update_config(key: str, value: Any) -> None:
    """Update a specific configuration value."""
    _config[key] = value

def get_config_summary() -> str:
    """Return a string summary of the current configuration."""
    return f"Seed: {_config['random_seed']}, RAM: {_config['max_ram_gb']}GB, Batch: {_config['batch_size']}"

def get_path(name: str) -> Path:
    """Resolve a path relative to the project root based on a logical name."""
    path_map = {
        "root": _PROJECT_ROOT,
        "code": _PROJECT_ROOT / "code",
        "data": _PROJECT_ROOT / "data",
        "data_raw": _PROJECT_ROOT / "data" / "raw",
        "data_processed": _PROJECT_ROOT / "data" / "processed",
        "data_test": _PROJECT_ROOT / "data" / "test",
        "specs": _PROJECT_ROOT / "specs",
        "docs": _PROJECT_ROOT / "docs",
        "tests": _PROJECT_ROOT / "tests",
    }
    if name not in path_map:
        raise ValueError(f"Unknown path name: {name}")
    return path_map[name]

def get_output_path(name: str) -> Path:
    """Get a path specifically for output artifacts (usually in data/processed)."""
    return get_path("data_processed") / name

def ensure_directories() -> None:
    """Ensure all standard project directories exist."""
    dirs = [
        get_path("code"),
        get_path("data_raw"),
        get_path("data_processed"),
        get_path("data_test"),
        get_path("specs"),
        get_path("docs"),
        get_path("tests"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_batch_size() -> int:
    """Return the configured batch size."""
    return _config["batch_size"]

def get_max_memory_gb() -> int:
    """Return the configured maximum RAM in GB."""
    return _config["max_ram_gb"]

def get_drift_threshold() -> float:
    """Return the configured drift threshold."""
    return _config["drift_threshold"]

def get_centroid_model() -> str:
    """Return the configured centroid model name."""
    return _config["centroid_model"]

def get_baseline_model() -> str:
    """Return the configured baseline model name."""
    return _config["baseline_model"]
