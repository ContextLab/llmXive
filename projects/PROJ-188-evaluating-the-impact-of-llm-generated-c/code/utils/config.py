import os
from pathlib import Path
from typing import Final

# Project root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

# Paths
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DIR: Final[Path] = DATA_DIR / "raw"
INTERMEDIATE_DIR: Final[Path] = DATA_DIR / "intermediate"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"

# Constants
MAX_TOKENS: Final[int] = 150
TIMEOUT_SECONDS: Final[int] = 300
SEED: Final[int] = 42

def ensure_dirs_exist() -> None:
    """Create data directories if they don't exist."""
    for dir_path in [RAW_DIR, INTERMEDIATE_DIR, PROCESSED_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
