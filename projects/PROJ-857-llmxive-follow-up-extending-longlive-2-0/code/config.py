import os
import sys
from pathlib import Path
from typing import Final, List, Dict, Any, Optional

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RESULTS_DIR: Final[Path] = DATA_DIR / "results"
FIGURES_DIR: Final[Path] = DATA_DIR / "figures"

# Bit-widths supported
BIT_WIDTHS: Final[List[int]] = [2, 4, 8]

# Seeds for reproducibility
DEFAULT_SEED: Final[int] = 42
SEEDS: Final[List[int]] = [42, 123, 456]

# Path configurations
def get_path_str(path: Path) -> str:
    """Converts a Path object to a string."""
    return str(path)

def ensure_dirs_exist():
    """Creates necessary directories if they do not exist."""
    for dir_path in [DATA_DIR, RESULTS_DIR, FIGURES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
