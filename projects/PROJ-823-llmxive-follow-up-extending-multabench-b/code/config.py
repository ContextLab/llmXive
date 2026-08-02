import os
from pathlib import Path

# Global configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Seeds
RANDOM_SEED = 42
SENSITIVITY_SEEDS = [42, 123, 456, 789, 101]

def ensure_directories(dirs: list):
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
