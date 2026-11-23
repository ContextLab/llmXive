import os
import random
import numpy as np
import logging
from pathlib import Path
from typing import Final, Dict, Any

# Constants
MAX_TOKENS: Final[int] = 200
TIMEOUT_SECONDS: Final[int] = 300
SEED: Final[int] = 42
RAM_THRESHOLD_GB: Final[float] = 7.0

# Paths
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
DATA_ROOT: Final[Path] = PROJECT_ROOT / "data"
DATA_RAW: Final[Path] = DATA_ROOT / "raw"
DATA_INTERMEDIATE: Final[Path] = DATA_ROOT / "intermediate"
DATA_PROCESSED: Final[Path] = DATA_ROOT / "processed"
FIGURES_DIR: Final[Path] = PROJECT_ROOT / "figures"

# Model Configuration
MODEL_PRIMARY: Final[str] = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MODEL_FALLBACK: Final[str] = "codellama/CodeLlama-7b-hf"
MAX_NEW_TOKENS: Final[int] = 200

# Statistical Power
# Targeting sufficient power for GLMM interaction effects (alpha=0.05, power=0.8)
# Based on standard G*Power estimates for mixed models with 3 conditions
MIN_PARTICIPANTS: Final[int] = 42
MIN_RESPONSES_PER_PARTICIPANT: Final[int] = 3

def set_seed(seed: int = SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    logging.info(f"Random seed set to {seed}")

def ensure_dirs_exist():
    """Ensure required directories exist."""
    dirs = [
        str(DATA_RAW),
        str(DATA_INTERMEDIATE),
        str(DATA_PROCESSED),
        str(FIGURES_DIR)
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logging.debug(f"Ensured directory exists: {d}")

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "max_tokens": MAX_TOKENS,
        "timeout_seconds": TIMEOUT_SECONDS,
        "seed": SEED,
        "ram_threshold_gb": RAM_THRESHOLD_GB,
        "model_primary": MODEL_PRIMARY,
        "model_fallback": MODEL_FALLBACK,
        "min_participants": MIN_PARTICIPANTS,
        "paths": {
            "data_raw": str(DATA_RAW),
            "data_intermediate": str(DATA_INTERMEDIATE),
            "data_processed": str(DATA_PROCESSED),
            "figures": str(FIGURES_DIR)
        }
    }