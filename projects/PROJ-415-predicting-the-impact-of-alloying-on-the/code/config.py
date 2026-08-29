import os
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Directories
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
MODELS_DIR: Final[Path] = PROJECT_ROOT / "models"
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
LOG_DIR: Final[Path] = DATA_DIR / "logs"
ERRORS_DIR: Final[Path] = PROJECT_ROOT / "errors"
FIGURES_DIR: Final[Path] = PROJECT_ROOT / "figures"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# Sub-directories for data
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
CURATED_DATA_DIR: Final[Path] = DATA_DIR / "curated"
ARTIFACTS_DIR: Final[Path] = DATA_DIR / "artifacts"

# Configuration Constants
RANDOM_SEED: Final[int] = 42
TARGET_POWER: Final[float] = 0.80
ALPHA: Final[float] = 0.05

def ensure_directories() -> None:
    """
    Ensures all required directories exist.
    This is a helper for initialization scripts.
    """
    import os
    dirs = [
        CODE_DIR, TESTS_DIR, DATA_DIR, MODELS_DIR, REPORTS_DIR,
        LOG_DIR, ERRORS_DIR, FIGURES_DIR, CONTRACTS_DIR,
        RAW_DATA_DIR, CURATED_DATA_DIR, ARTIFACTS_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
