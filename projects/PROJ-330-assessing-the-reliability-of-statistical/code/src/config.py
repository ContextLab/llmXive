import os
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CODE_ROOT: Final[Path] = PROJECT_ROOT / "code"
DATA_ROOT: Final[Path] = PROJECT_ROOT / "data"
FIGURES_ROOT: Final[Path] = PROJECT_ROOT / "figures"
STATE_FILE: Final[Path] = PROJECT_ROOT / "state.yaml"

# Runtime thresholds
MAX_RUNTIME_HOURS: Final[int] = 6
MIN_PERMUTATIONS: Final[int] = 100

# Random seeds for reproducibility
RANDOM_SEED: Final[int] = 42

def ensure_directories() -> None:
    """Create required project directories if they do not exist."""
    for directory in [CODE_ROOT, DATA_ROOT, FIGURES_ROOT]:
        directory.mkdir(parents=True, exist_ok=True)
