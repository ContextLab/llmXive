import os
from pathlib import Path
from typing import Final

# Configuration constants
SEED: Final[int] = 42
MAX_TOKENS: Final[int] = 200
TIMEOUT_SECONDS: Final[int] = 300
MAX_MEMORY_GB: Final[int] = 7

# Paths
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DIR: Final[Path] = DATA_DIR / "raw"
INTERMEDIATE_DIR: Final[Path] = DATA_DIR / "intermediate"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"

# Ensure directories exist
def ensure_dirs_exist() -> None:
    """Create data directories if they don't exist."""
    for dir_path in [DATA_DIR, RAW_DIR, INTERMEDIATE_DIR, PROCESSED_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Initialize directories
ensure_dirs_exist()
