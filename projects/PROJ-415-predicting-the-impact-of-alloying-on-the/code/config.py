import os
import random
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_CURATED_DIR: Final[Path] = DATA_DIR / "curated"
DATA_MOCK_DIR: Final[Path] = DATA_DIR / "mock"
MODELS_DIR: Final[Path] = PROJECT_ROOT / "models"
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
ERRORS_DIR: Final[Path] = PROJECT_ROOT / "errors"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"

# Specific paths for convenience
CURATED_DIR: Final[Path] = DATA_CURATED_DIR
RAW_DIR: Final[Path] = DATA_RAW_DIR

# Configuration
RANDOM_SEED: Final[int] = 42

def ensure_directories() -> None:
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_DIR, DATA_RAW_DIR, DATA_CURATED_DIR, DATA_MOCK_DIR,
        MODELS_DIR, REPORTS_DIR, ERRORS_DIR, LOGS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_global_seed(seed: int = RANDOM_SEED) -> None:
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeding handled in specific modules if needed
    
# Filter Criteria
FILTER_CRITERIA: Final[dict] = {
    'crystal_structure': 'FCC',
    'diffusion_mode': 'self'
}

# Data Streaming Config (from T056)
DATA_STREAMING_CONFIG: Final[dict] = {
    'STREAMING_CHUNK_SIZE': 1000,
    'MAX_MEMORY_MB': 6000,
    'MIN_DATASET_SIZE_FOR_SPLIT': 20,
    'MIN_DATASET_SIZE_FOR_VALIDATION': 50
}

# Initialize directories on import if not already done
# This ensures paths exist for scripts that import config but don't run setup
ensure_directories()
