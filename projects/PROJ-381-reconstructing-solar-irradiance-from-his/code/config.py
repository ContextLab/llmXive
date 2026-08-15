import os
from pathlib import Path
from typing import Final

from env_manager import setup_environment, get_data_path

# Initialize environment paths
PATHS = setup_environment()

# Project root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Data paths
DATA_ROOT: Final[Path] = PATHS['data_root']
RAW_DATA_DIR: Final[Path] = PATHS['raw']
PROCESSED_DATA_DIR: Final[Path] = PATHS['processed']
FIGURES_DIR: Final[Path] = PATHS['figures']

# Model artifacts directory
MODELS_DIR: Final[Path] = PROJECT_ROOT / "code" / "models" / "artifacts"

# Contracts directory
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# Specs directory
SPECS_DIR: Final[Path] = PROJECT_ROOT / "specs"

# Random seeds
RANDOM_SEED: Final[int] = 42

# FR-002 Gap logic constants
GAP_THRESHOLD_YEARS: Final[float] = 1.0
GAP_PROXY_GSN: Final[int] = 0

# FR-009 Thresholds
INCONSISTENCY_TOLERANCE_THRESHOLDS: Final[list] = [0.01, 0.05, 0.1]

# Bootstrap iterations (FR-005)
BOOTSTRAP_ITERATIONS: Final[int] = 1000

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for path in [DATA_ROOT, RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR, MODELS_DIR, CONTRACTS_DIR, SPECS_DIR]:
        path.mkdir(parents=True, exist_ok=True)

# Re-export for backward compatibility if needed elsewhere
__all__ = [
    'PROJECT_ROOT', 'DATA_ROOT', 'RAW_DATA_DIR', 'PROCESSED_DATA_DIR', 
    'FIGURES_DIR', 'MODELS_DIR', 'CONTRACTS_DIR', 'SPECS_DIR',
    'RANDOM_SEED', 'GAP_THRESHOLD_YEARS', 'GAP_PROXY_GSN',
    'INCONSISTENCY_TOLERANCE_THRESHOLDS', 'BOOTSTRAP_ITERATIONS',
    'ensure_directories'
]