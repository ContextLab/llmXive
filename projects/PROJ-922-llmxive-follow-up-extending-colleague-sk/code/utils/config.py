import os
import random
from pathlib import Path
from typing import Optional
import numpy as np

# Configuration Constants
# Derived from T000a (Spec Amendment) and T000b (Application)
GLMM_AUTHORIZED = True

# SC-002: Non-Inferiority Margin for Style Consistency
# Defined as a small, predefined absolute percentage point threshold (5%).
# Used in hypothesis verification and statistical analysis (T028, T032, T042).
NON_INFERIORITY_MARGIN = 0.05  # 5 percentage points as per SC-002

# Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
FIGURES_DIR = PROJECT_ROOT / "data" / "processed" / "figures"

# Global Seed
GLOBAL_SEED = 42

def set_global_seed(seed: int = GLOBAL_SEED) -> None:
    """Set global seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_code_dir() -> Path:
    return CODE_DIR

def get_data_dir() -> Path:
    return DATA_DIR

def get_tests_dir() -> Path:
    return TESTS_DIR

def get_state_dir() -> Path:
    return STATE_DIR

def get_figures_dir() -> Path:
    return FIGURES_DIR

def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def get_config_from_env() -> dict:
    """Load configuration from environment variables."""
    return {
        "model_path": os.getenv("MODEL_PATH", "default_model"),
        "device": os.getenv("DEVICE", "cpu"),
    }

def get_device() -> str:
    """Get device from config or env."""
    # Local import to avoid breaking CPU-only runners if torch is not installed
    try:
        import torch
        env_device = os.getenv("DEVICE", "cpu")
        if env_device == "cuda" and not torch.cuda.is_available():
            return "cpu"
        return env_device
    except ImportError:
        return "cpu"

def get_model_cache_dir() -> Path:
    return get_data_dir() / "models" / "cache"

def get_output_path(filename: str) -> Path:
    """Get full path for an output file."""
    return DATA_DIR / "processed" / filename

# Ensure torch is imported only if needed for device checks, 
# but avoid hard dependency if not running on GPU.
# Note: torch import moved to local scope in functions that need it to avoid 
# breaking CPU-only runners if torch is not installed yet.
def check_torch_availability() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False