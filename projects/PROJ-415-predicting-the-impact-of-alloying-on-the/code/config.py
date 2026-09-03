import os
import random
from pathlib import Path
from typing import Final

# Try to import torch, but don't fail if it's not installed (CPU-only env)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
MODELS_DIR: Final[Path] = PROJECT_ROOT / "models"
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
ERRORS_DIR: Final[Path] = PROJECT_ROOT / "errors"
LOG_DIR: Final[Path] = PROJECT_ROOT / "data" / "logs"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"

RANDOM_SEED: Final[int] = 42

def ensure_directories():
    """Create all required directories if they do not exist."""
    dirs = [DATA_DIR, MODELS_DIR, REPORTS_DIR, ERRORS_DIR, LOG_DIR, TESTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_global_seed(seed: int = RANDOM_SEED) -> None:
    """
    Enforce a global random seed for reproducibility.
    Sets seeds for:
      - Python's built-in `random` module
      - `numpy`
      - `torch` (if available)
    
    Logs the seed to `data/logs/execution_log.txt` in the format:
    SEED: <value>
    """
    # Set Python random seed
    random.seed(seed)
    
    # Set numpy seed
    import numpy as np
    np.random.seed(seed)
    
    # Set torch seed if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    
    # Log the seed
    ensure_directories()
    log_path = LOG_DIR / "execution_log.txt"
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"SEED: {seed}\n")

# Execute seed setting immediately upon import to ensure reproducibility
# for any subsequent code execution in this pipeline.
set_global_seed(RANDOM_SEED)