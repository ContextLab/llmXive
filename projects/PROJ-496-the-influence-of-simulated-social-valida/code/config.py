"""
Configuration module for the Simulated Social Validation project.
Handles path management, environment variables, and reproducibility seeds.
"""
import os
import random
from pathlib import Path
from typing import Optional

# Project Root
# Assumes code/ is at projects/PROJ-496-.../code/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Paths ---
DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = _PROJECT_ROOT / "data" / "results"
FIGURES_DIR = _PROJECT_ROOT / "data" / "figures"
SPECS_DIR = _PROJECT_ROOT / "specs" / "main-feature-sim-social-validation"
CONTRACTS_DIR = SPECS_DIR / "contracts"

# --- Reproducibility (Constitution Principle I) ---
# Fixed seed for reproducibility across all random operations
RANDOM_SEED = 42

def set_seeds(seed: Optional[int] = None) -> None:
    """
    Pin random seeds for reproducibility.
    Must be called BEFORE any data loading or model fitting.
    
    Args:
        seed: Optional seed override. Defaults to RANDOM_SEED (42).
    """
    if seed is None:
        seed = RANDOM_SEED
    
    # Set Python random
    random.seed(seed)
    
    # Set NumPy (if available)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass  # numpy not installed yet, will be caught when needed
    
    # Set PyTorch (if available)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

# --- Environment ---
def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable with an optional default."""
    return os.getenv(key, default)

def ensure_dirs() -> None:
    """Ensure all required data directories exist."""
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, FIGURES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
