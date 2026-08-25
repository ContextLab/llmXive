import os
import random
from pathlib import Path
from typing import Optional

# Project root path
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory paths
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_DERIVED_DIR = BASE_DIR / "data" / "derived"
FIGURES_DIR = BASE_DIR / "figures"
SPECS_DIR = BASE_DIR / "specs"

# Random seeds for reproducibility
RANDOM_SEED = 42
NP_SEED = 42
TORCH_SEED = 42  # If torch is used later

# MAF threshold (Minor Allele Frequency) for filtering SNPs
# Only SNPs with MAF > 1% are kept
MAF_THRESHOLD = 0.01

# Ensure all required directories exist
def ensure_data_dirs():
    """Create the required project directory structure if it does not exist."""
    dirs = [
        BASE_DIR / "code",
        DATA_RAW_DIR,
        DATA_DERIVED_DIR,
        FIGURES_DIR,
        BASE_DIR / "tests",
        BASE_DIR / "tests" / "unit",
        BASE_DIR / "tests" / "integration",
        BASE_DIR / "tests" / "contract",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Ensure __init__.py exists in each package directory
        if d.name == "code" or d.parent.name in ("tests", "data"):
            init_file = d / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Auto-initialized package\n")

# NOTE: Window size is NOT defined here.
# Per FR-002 and T005 requirements, the window size MUST be derived dynamically
# from the loaded PWM length (len(pwm)) in the scoring engine (code/scoring.py).
# No fallback constants like DEFAULT_WINDOW are permitted.

def set_seeds():
    """Set random seeds for reproducibility across libraries."""
    random.seed(RANDOM_SEED)
    try:
        import numpy as np
        np.random.seed(NP_SEED)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(TORCH_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(TORCH_SEED)
    except ImportError:
        pass

# Initialize seeds on import if desired, or call set_seeds() explicitly
# set_seeds()
