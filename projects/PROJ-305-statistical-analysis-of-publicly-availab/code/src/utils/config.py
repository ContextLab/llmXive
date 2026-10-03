import os
from pathlib import Path
from typing import Dict, Final

# Project paths
PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Final = PROJECT_ROOT / "data"
OUTPUT_DIR: Final = PROJECT_ROOT / "output"
LOGS_DIR: Final = PROJECT_ROOT / "logs"
CODE_DIR: Final = PROJECT_ROOT / "code"

# Ensure directories exist
def ensure_dirs():
    """Create necessary directories if they don't exist."""
    for dir_path in [DATA_DIR, OUTPUT_DIR, LOGS_DIR]:
        os.makedirs(dir_path, exist_ok=True)

# Analysis thresholds (from T004)
# These are internal dataset-based thresholds for ROR, PRR, IC
# External background rates are NOT calculated (known limitation)
THRESHOLDS: Final[Dict[str, float]] = {
    "ror_min": 2.0,
    "ror_ci_min": 1.0,
    "prr_min": 1.5,
    "prr_ci_min": 1.0,
    "ic_min": 0.0,
    "ic_ci_min": 0.0
}

# Memory limits (from T039, T040)
MEMORY_LIMIT_CLEANING_GB: Final[float] = 5.0
MEMORY_LIMIT_ANALYSIS_GB: Final[float] = 7.0

# Random seed for reproducibility
RANDOM_SEED: Final[int] = 42

# MedDRA mapping file path
MEDDRA_MAPPING_PATH: Final[Path] = DATA_DIR / "meddra_soc_mapping.csv"
