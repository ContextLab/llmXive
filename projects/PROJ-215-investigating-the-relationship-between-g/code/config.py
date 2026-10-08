import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import yaml

# Global configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INTERIM_DIR = DATA_DIR / "interim"
INTERIOR_DIR = DATA_DIR / "interior"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"
STATE_DIR = PROJECT_ROOT / "state"

# Default thresholds
PREVALENCE_THRESHOLD = 0.001  # 0.1%
RAREFACTION_LOSS_THRESHOLD = 0.20  # 20%
MIN_SAMPLES_RETENTION = 100

def ensure_directories():
    """Create necessary directories if they don't exist."""
    dirs = [DATA_DIR, RAW_DIR, PROCESSED_DIR, INTERIM_DIR, INTERIOR_DIR, RESULTS_DIR, LOGS_DIR, STATE_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_random_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def get_output_path(filename: str) -> str:
    """
    Resolve a relative path to an absolute path within the project.
    
    This function handles multiple call patterns observed across the codebase:
    1. get_output_path("data/processed/file.csv") -> returns full path
    2. get_output_path("data/processed") -> returns directory path
    3. get_output_path() -> returns project root (fallback)
    4. get_output_path("results") -> returns results dir
    
    Args:
        filename: Relative path from project root or just a filename.
                
    Returns:
        Absolute path string.
    """
    if filename is None:
        return str(PROJECT_ROOT)
    
    # Handle empty string or just directory names
    if filename == "" or filename == ".":
        return str(PROJECT_ROOT)
    
    # Check if it's a known directory key
    if filename in ["data", "raw", "processed", "interim", "interior", "results", "logs", "state"]:
        dir_map = {
            "data": DATA_DIR,
            "raw": RAW_DIR,
            "processed": PROCESSED_DIR,
            "interim": INTERIM_DIR,
            "interior": INTERIOR_DIR,
            "results": RESULTS_DIR,
            "logs": LOGS_DIR,
            "state": STATE_DIR
        }
        return str(dir_map[filename])
    
    # Handle relative paths
    if filename.startswith("/"):
        return filename
    
    # Construct path relative to project root
    full_path = PROJECT_ROOT / filename
    return str(full_path)

def calculate_median_depth(counts_array: np.ndarray) -> float:
    """Calculate median sequencing depth from a 2D count array."""
    depths = np.sum(counts_array, axis=1)
    return float(np.median(depths[depths > 0])) if np.any(depths > 0) else 0.0

def estimate_rarefaction_loss(depths: np.ndarray, target_depth: float) -> float:
    """Estimate sample loss rate for a given rarefaction depth."""
    lost = np.sum(depths < target_depth)
    total = len(depths)
    return lost / total if total > 0 else 0.0

def load_config() -> Dict[str, Any]:
    """Load configuration from state/seeds.yaml if it exists."""
    seeds_path = STATE_DIR / "seeds.yaml"
    if seeds_path.exists():
        with open(seeds_path, 'r') as f:
            return yaml.safe_load(f)
    return {}
