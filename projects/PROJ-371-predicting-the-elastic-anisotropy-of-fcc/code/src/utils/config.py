"""
Configuration management for the elastic anisotropy prediction pipeline.

This module manages:
- File system paths (data/raw, data/processed, output)
- Random seeds for reproducibility
- Constants used across the pipeline
- Environment variable loading for API keys
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to load dotenv if available, but don't fail if not present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional; if not installed, we just proceed without it
    pass

# Project root is the parent of the 'code' directory (assuming code/ is at repo root)
# If the project structure is different, adjust accordingly.
# Based on tasks.md, the project structure uses 'src/' at repository root.
# However, the task description says "Create src/utils/config.py".
# The "Existing project API surface" shows files under "code/tests/...".
# Let's assume the project root is the directory containing 'code', 'data', 'tests'.
# But wait, tasks.md says: "Paths shown below assume single project - adjust based on plan.md structure"
# and "Single project: src/, tests/ at repository root".
# The task T004 specifically asks for `src/utils/config.py`.
# The completed tasks T001-T003 created the structure.
# Let's assume the current working directory when running scripts is the project root.
# We will define paths relative to the project root.

# Determine project root: look for 'data' and 'src' directories in the current working directory
# or parent directories.
def _find_project_root() -> Path:
    """Find the project root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "src").exists() and (current / "data").exists() and (current / "tests").exists():
            return current
        current = current.parent
    # Fallback: assume current directory is root if we can't find the structure
    return Path.cwd()

PROJECT_ROOT = _find_project_root()

# Path constants
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = PROJECT_ROOT / "output" / "figures"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Random seed for reproducibility
RANDOM_SEED: int = 42

# Constants
# Elastic anisotropy bounds for FCC metals (theoretical range)
ANISOTROPY_LOWER_BOUND: float = 0.0
ANISOTROPY_UPPER_BOUND: float = 3.0

# API Key environment variable names
MP_API_KEY_ENV_VAR: str = "MP_API_KEY"
AFLOW_API_KEY_ENV_VAR: str = "AFLOW_API_KEY"  # If AFLOW requires an API key

# Default parameters for data ingestion
MIN_UNIQUE_ENTRIES: int = 50  # SC-001: Verify >= 50 unique entries

# Model training parameters
TRAIN_TEST_SPLIT_RATIO: float = 0.8  # Spec's assumption, though LOEO is used
MAX_TRAINING_TIME_HOURS: float = 1.0  # US-2 Acceptance 1

# Sensitivity analysis parameters
OUTLIER_STD_DEVS: List[float] = [2.5, 3.0, 3.5]  # FR-005
SENSITIVITY_VARIANCE_THRESHOLD: float = 0.1  # US-3 Acceptance 2

# Configuration dictionary for easy access
CONFIG: Dict[str, Any] = {
    "paths": {
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "output": str(OUTPUT_DIR),
        "figures": str(FIGURES_DIR),
    },
    "random_seed": RANDOM_SEED,
    "constants": {
        "anisotropy_lower_bound": ANISOTROPY_LOWER_BOUND,
        "anisotropy_upper_bound": ANISOTROPY_UPPER_BOUND,
        "min_unique_entries": MIN_UNIQUE_ENTRIES,
        "max_training_time_hours": MAX_TRAINING_TIME_HOURS,
        "sensitivity_variance_threshold": SENSITIVITY_VARIANCE_THRESHOLD,
    },
    "api_keys": {
        "materials_project": os.getenv(MP_API_KEY_ENV_VAR),
        "aflow": os.getenv(AFLOW_API_KEY_ENV_VAR),
    },
}


def get_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return CONFIG.copy()


def get_path(key: str) -> Path:
    """
    Get a path from the configuration.

    Args:
        key: One of 'data_raw', 'data_processed', 'output', 'figures'.

    Returns:
        Path object for the requested directory.
    """
    path_map = {
        "data_raw": DATA_RAW_DIR,
        "data_processed": DATA_PROCESSED_DIR,
        "output": OUTPUT_DIR,
        "figures": FIGURES_DIR,
    }
    if key not in path_map:
        raise KeyError(f"Invalid path key: {key}. Must be one of {list(path_map.keys())}")
    return path_map[key]


def validate_api_keys() -> bool:
    """
    Validate that required API keys are present in the environment.

    Returns:
        True if all required keys are present, False otherwise.
    """
    required_keys = [MP_API_KEY_ENV_VAR]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    if missing_keys:
        print(f"Warning: Missing required API keys: {', '.join(missing_keys)}")
        return False
    return True


def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility.

    Args:
        seed: The random seed to use. If None, uses the default (42).
    """
    global RANDOM_SEED
    if seed is not None:
        RANDOM_SEED = seed
    # Note: This function only updates the constant.
    # Callers must ensure they use this constant when setting seeds for numpy, torch, etc.


def get_seed() -> int:
    """Return the current random seed."""
    return RANDOM_SEED
