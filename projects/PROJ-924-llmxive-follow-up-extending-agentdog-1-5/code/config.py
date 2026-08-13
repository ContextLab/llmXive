import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List
import numpy as np

# Configuration constants
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64

# Model configurations
CENTROID_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BASELINE_MODEL = "google/flan-t5-small"

# Path configuration
_PATHS = {
    "project_root": Path(__file__).resolve().parent.parent,
    "code": "code",
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "data_test": "data/test",
    "specs": "specs",
    "docs": "docs",
    "raw_taxonomy": "data/processed/taxonomy_agentdog.json",
    "checksums": "data/checksums.json",
}

_config: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": BATCH_SIZE,
    "centroid_model": CENTROID_MODEL,
    "baseline_model": BASELINE_MODEL,
    "paths": _PATHS,
}

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_config() -> Dict[str, Any]:
    """Return the current configuration."""
    return _config.copy()

def update_config(key: str, value: Any) -> None:
    """Update a configuration value."""
    _config[key] = value

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the configuration for logging."""
    return {
        "random_seed": _config["random_seed"],
        "max_ram_gb": _config["max_ram_gb"],
        "batch_size": _config["batch_size"],
        "centroid_model": _config["centroid_model"],
        "baseline_model": _config["baseline_model"],
    }

def get_path(name: str) -> Path:
    """
    Get a path from the configuration.
    Raises KeyError if the path name is not found.
    """
    if name not in _config["paths"]:
        raise KeyError(f"Path '{name}' not found in configuration.")
    base = _config["paths"]["project_root"]
    path_str = _config["paths"][name]
    return base / path_str

def get_output_path(name: str, filename: str) -> Path:
    """Get an output path combining a directory name and filename."""
    dir_path = get_path(name)
    return dir_path / filename

def ensure_directories(paths: List[Path]) -> None:
    """Ensure that the given paths exist as directories."""
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def get_batch_size() -> int:
    """Return the configured batch size."""
    return _config["batch_size"]

def get_max_memory_gb() -> float:
    """Return the configured maximum RAM in GB."""
    return _config["max_ram_gb"]

def get_drift_threshold() -> float:
    """Return the drift threshold for flagging reviews."""
    return 1.5  # Default threshold

def get_centroid_model() -> str:
    """Return the configured centroid model name."""
    return _config["centroid_model"]

def get_baseline_model() -> str:
    """Return the configured baseline model name."""
    return _config["baseline_model"]
