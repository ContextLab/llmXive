import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import numpy as np

# Configuration constants
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64  # Source: arxiv.org/abs/2410.21676

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Default paths
PATHS = {
    "data": PROJECT_ROOT / "data",
    "raw_data": PROJECT_ROOT / "data" / "raw",
    "processed": PROJECT_ROOT / "data" / "processed",
    "test": PROJECT_ROOT / "data" / "test",
    "specs": PROJECT_ROOT / "specs",
    "docs": PROJECT_ROOT / "docs",
    "code": PROJECT_ROOT / "code",
    "project_root": PROJECT_ROOT,
    "checksums": PROJECT_ROOT / "data" / "checksums.json",
    "centroid_file": PROJECT_ROOT / "data" / "processed" / "taxonomy_centroids.json",
    "drift_scores_csv": PROJECT_ROOT / "data" / "processed" / "drift_scores.csv",
    "data_test": PROJECT_ROOT / "data" / "test",
    "output_dir": PROJECT_ROOT / "data" / "processed",
}

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return {
        "random_seed": RANDOM_SEED,
        "max_ram_gb": MAX_RAM_GB,
        "batch_size": BATCH_SIZE,
    }

def update_config(key: str, value: Any) -> None:
    """Update configuration value."""
    global RANDOM_SEED, MAX_RAM_GB, BATCH_SIZE
    if key == "random_seed":
        RANDOM_SEED = value
    elif key == "max_ram_gb":
        MAX_RAM_GB = value
    elif key == "batch_size":
        BATCH_SIZE = value

def get_config_summary() -> str:
    """Get a summary of the configuration."""
    return f"Seed: {RANDOM_SEED}, Max RAM: {MAX_RAM_GB}GB, Batch Size: {BATCH_SIZE}"

def get_path(*args: Union[str, Path]) -> Path:
    """
    Get a path from the configuration.
    
    This function handles multiple calling patterns:
    - get_path("key") where key is in PATHS
    - get_path("data", "processed") to build paths from components
    - get_path("data", "processed", "file.csv") for nested paths
    
    Args:
        *args: Path components or a single key from PATHS.
    
    Returns:
        A Path object.
    
    Raises:
        KeyError: If the key is not found in PATHS and args don't form a valid path.
    """
    if len(args) == 1:
        key = args[0]
        if isinstance(key, Path):
            return key
        if key in PATHS:
            return PATHS[key]
        # If not in PATHS, treat as a relative path from project root
        return PROJECT_ROOT / key
    else:
        # Build path from multiple components
        base = PROJECT_ROOT
        for arg in args:
            base = base / arg
        return base

def get_output_path(name: str) -> Path:
    """Get an output path for a named artifact."""
    return PROJECT_ROOT / "data" / "processed" / name

def ensure_directories(paths: List[Union[str, Path]]) -> None:
    """Ensure directories exist."""
    for path in paths:
        if isinstance(path, str):
            path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

def get_batch_size() -> int:
    """Get the batch size."""
    return BATCH_SIZE

def get_max_memory_gb() -> int:
    """Get the maximum memory in GB."""
    return MAX_RAM_GB

def get_drift_threshold() -> float:
    """Get the drift threshold."""
    return 0.5

def get_centroid_model() -> str:
    """Get the centroid model name."""
    return "all-MiniLM-L6-v2"

def get_baseline_model() -> str:
    """Get the baseline model name."""
    return "google/flan-t5-small"
