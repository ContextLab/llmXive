import os
import random
from pathlib import Path
from typing import Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_DERIVED_DIR = DATA_DIR / "derived"
FIGURES_DIR = PROJECT_ROOT / "figures"

def ensure_data_dirs():
    """Create data directories if they don't exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def set_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds would be set here if imported
    # import numpy as np
    # np.random.seed(seed)

# Configuration constants
MAF_THRESHOLD = 0.01  # 1%
DEFAULT_GENOME_BUILD = "GRCh38"
