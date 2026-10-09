import os
import random
from typing import Set

# ----------------------------------------------------------------------
# Core project paths
# ----------------------------------------------------------------------
# Project root directory (the directory containing this config file's parent)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Standard data directories
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
INTERIM_DIR = os.path.join(PROJECT_ROOT, "data", "interim")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

# Ensure directories exist when the config is imported (helps downstream scripts)
for _dir in (RAW_DIR, INTERIM_DIR, PROCESSED_DIR, REPORTS_DIR):
    os.makedirs(_dir, exist_ok=True)

# ----------------------------------------------------------------------
# Resource limits and analysis parameters
# ----------------------------------------------------------------------
# Maximum RAM usage allowed for the pipeline (GB)
MAX_RAM_GB = 7

# Alpha levels used for the sensitivity sweep (FDR / significance thresholds)
ALPHA_SET: Set[float] = {0.01, 0.05, 0.1}

# Fixed random seed for reproducibility
SEED = 42
# Preserve the older name for backward compatibility
RANDOM_SEED = SEED

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def set_random_seed(seed: int = SEED):
    """
    Set the global random seed for both the Python ``random`` module
    and NumPy (if it has been imported). This function is idempotent
    and can be called early in any script that requires deterministic
    behaviour.
    """
    random.seed(seed)
    # If NumPy is already imported elsewhere we also seed it.
    if "numpy" in globals() or "numpy" in locals():
        import numpy as np
        np.random.seed(seed)

def get_path(key: str) -> str:
    """
    Retrieve a path based on a symbolic key. Supported keys:

        - "project_root": the root of the repository
        - "raw":          RAW_DIR
        - "interim":      INTERIM_DIR
        - "processed":    PROCESSED_DIR
        - "reports":      REPORTS_DIR

    Any unknown key returns an empty string.
    """
    paths = {
        "project_root": PROJECT_ROOT,
        "raw": RAW_DIR,
        "interim": INTERIM_DIR,
        "processed": PROCESSED_DIR,
        "reports": REPORTS_DIR,
    }
    return paths.get(key, "")

def get_alpha_set() -> Set[float]:
    """Return the set of alpha thresholds for sensitivity analysis."""
    return ALPHA_SET

def get_memory_threshold_mb() -> int:
    """Return the memory threshold in megabytes (convenient for libs that use MB)."""
    return MAX_RAM_GB * 1024