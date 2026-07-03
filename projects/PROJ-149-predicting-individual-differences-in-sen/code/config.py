"""
Configuration constants for the EEG analysis pipeline.
"""
import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"
CODE_UTILS = CODE_DIR / "utils"
TESTS_DIR = PROJECT_ROOT / "tests"

# Random Seed
RANDOM_SEED = 42

# Filter Parameters
FILTER_LOW = 1.0  # Hz
FILTER_HIGH = 40.0  # Hz
NOTCH_FREQ = 50  # Hz (or 60 depending on region, set to 50 as default)

# Band Definitions (Hz)
BAND_FREQS: Dict[str, Tuple[float, float]] = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "low_beta": (13.0, 20.0),
    "high_beta": (20.0, 30.0),
    "gamma": (30.0, 40.0)
}

def ensure_dirs():
    """Create necessary directories if they don't exist."""
    for d in [DATA_RAW, DATA_INTERIM, DATA_PROCESSED, CODE_DIR, CODE_UTILS, TESTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def set_global_seed(seed: int = RANDOM_SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_path(category: str, filename: str = None) -> Path:
    """
    Construct a path based on category.
    
    Categories:
    - raw, interim, processed, features_raw, processed_features_raw, etc.
    """
    base_map = {
        "raw": DATA_RAW,
        "interim": DATA_INTERIM,
        "interim_preprocessed_eeg": DATA_INTERIM / "preprocessed_eeg",
        "processed": DATA_PROCESSED,
        "processed_features_raw": DATA_PROCESSED / "features_raw.csv",
        "processed_features": DATA_PROCESSED / "features.csv",
    }
    
    base = base_map.get(category, DATA_PROCESSED)
    
    if filename:
        return base / filename
    return base

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Return the frequency bands dictionary."""
    return BAND_FREQS

def get_all_band_names() -> List[str]:
    """Return list of band names."""
    return list(BAND_FREQS.keys())
