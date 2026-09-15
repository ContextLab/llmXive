import os
from pathlib import Path

# Constants
RANDOM_SEED = 42
DATA_ROOT = "data"
RESULTS_ROOT = "results"

def ensure_directories():
    """Create required project directories if they don't exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "results/models",
        "results/figures",
        "tests",
        "contracts",
        "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directory is tracked
        gitkeep = Path(d) / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
