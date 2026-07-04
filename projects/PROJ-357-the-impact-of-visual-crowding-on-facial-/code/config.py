import os
import random
from pathlib import Path
from typing import Optional, Dict, Any

# Default RAVDESS configuration (resolved in T011a)
RAVDESS_DEFAULT_URL = "parlance/RAVDESS"
RAVDESS_DATASET_NAME = "parlance/RAVDESS"

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_seed() -> int:
    """Retrieve the random seed from environment or default."""
    seed = os.environ.get("RANDOM_SEED", "42")
    try:
        return int(seed)
    except ValueError:
        return 42

def set_all_seeds(seed: Optional[int] = None):
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: numpy and torch seeds are set where those libraries are imported

def ensure_directories(dirs: Optional[list] = None):
    """Ensure required directories exist."""
    if dirs is None:
        dirs = [
            PROJECT_ROOT / "data" / "raw",
            PROJECT_ROOT / "data" / "interim",
            PROJECT_ROOT / "data" / "processed",
            PROJECT_ROOT / "artifacts",
            PROJECT_ROOT / "state"
        ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        "data_dir": os.environ.get("DATA_DIR", str(PROJECT_ROOT / "data")),
        "artifacts_dir": os.environ.get("ARTIFACTS_DIR", str(PROJECT_ROOT / "artifacts")),
        "seed": get_seed(),
        "ravdess_url": os.environ.get("RAVDESS_URL", RAVDESS_DEFAULT_URL),
    }