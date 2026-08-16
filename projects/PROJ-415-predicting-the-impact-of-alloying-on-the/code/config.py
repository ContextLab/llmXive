import os
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
DATA_DIR: Final = PROJECT_ROOT / "data"
LOG_DIR: Final = DATA_DIR / "logs"
ERRORS_DIR: Final = PROJECT_ROOT / "errors"
MODELS_DIR: Final = PROJECT_ROOT / "models"
REPORTS_DIR: Final = PROJECT_ROOT / "reports"

# Random seeds for reproducibility
RANDOM_SEED: Final = 42

def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    """
    dirs = [DATA_DIR, LOG_DIR, ERRORS_DIR, MODELS_DIR, REPORTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Dir: {DATA_DIR}")
    print(f"Log Dir: {LOG_DIR}")
    print(f"Error Dir: {ERRORS_DIR}")
