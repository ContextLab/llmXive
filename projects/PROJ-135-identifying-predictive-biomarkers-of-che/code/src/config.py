import os
from pathlib import Path
from typing import Final

# Project root is assumed to be the parent of the 'code' directory in this structure
# Adjust based on actual project layout if needed
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if not (_PROJECT_ROOT / "data").exists():
    # Fallback if run from code/src
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    """Return the project root path."""
    return _PROJECT_ROOT

def ensure_directories() -> None:
    """Create required project directories if they don't exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "results",
        root / "results" / "meta_analysis",
        root / "tests",
        root / "specs" / "001-chemo-biomarker-discovery" / "contracts",
        root / "state" / "projects",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Configuration constants
RANDOM_SEED: Final[int] = 42
FDR_THRESHOLD: Final[float] = 0.05
LOG2FC_THRESHOLD: Final[float] = 1.0
MAX_VARIANCE_GENES: Final[int] = 5000
CPU_LIMIT: Final[int] = 4
MEMORY_LIMIT_MB: Final[int] = 8000
TIMEOUT_HOURS: Final[int] = 24