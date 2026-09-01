import os
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
MODELS_DIR: Final[Path] = PROJECT_ROOT / "models"
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
ERRORS_DIR: Final[Path] = PROJECT_ROOT / "errors"
LOG_DIR: Final[Path] = PROJECT_ROOT / "data" / "logs"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"

RANDOM_SEED: Final[int] = 42

def ensure_directories():
    """Create all required directories if they do not exist."""
    dirs = [DATA_DIR, MODELS_DIR, REPORTS_DIR, ERRORS_DIR, LOG_DIR, TESTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
