"""
Configuration management for the pain sensitivity prediction pipeline.
Provides directory paths, environment variable helpers, and global settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict

# ----------------------------------------------------------------------
# Project root
# ----------------------------------------------------------------------
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# Directory structure paths (absolute)
# ----------------------------------------------------------------------
DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = _PROJECT_ROOT / "artifacts"
STATE_DIR = _PROJECT_ROOT / "state"
CODE_DIR = _PROJECT_ROOT / "code"
TESTS_DIR = _PROJECT_ROOT / "tests"
SPECS_DIR = _PROJECT_ROOT / "specs"

# Mapping of logical directory keys to their relative paths.
# Used by tests to verify get_dir() functionality.
_DIRS: Dict[str, str] = {
    "raw": "data/raw",
    "processed": "data/processed",
    "artifacts": "artifacts",
    "state": "state",
    "code": "code",
    "tests": "tests",
    "specs": "specs",
}

# ----------------------------------------------------------------------
# File paths used by other modules
# ----------------------------------------------------------------------
STATE_FILE = STATE_DIR / "projects" / "PROJ-712-predicting-individual-pain-sensitivity-f.yaml"
DATASET_SCHEMA = _PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
FEATURES_SCHEMA = _PROJECT_ROOT / "contracts" / "features.schema.yaml"

# ----------------------------------------------------------------------
# Execution limits (from SC-005)
# ----------------------------------------------------------------------
MAX_EXECUTION_HOURS = 6
MAX_EXECUTION_SECONDS = MAX_EXECUTION_HOURS * 3600

# ----------------------------------------------------------------------
# Default experimental parameters
# ----------------------------------------------------------------------
DEFAULT_SEED = 42  # used by tests when LLMXIVE_SEED is unset
DEFAULT_MAX_ITER = 1000  # arbitrary sensible default for iterative algorithms
DEFAULT_RANDOM_SEED = DEFAULT_SEED  # retained for backward compatibility
DEFAULT_N_FOLDS = 5
DEFAULT_PERMUTATIONS = 100  # Minimum for global permutation test
DEFAULT_BOOTSTRAP_ITERATIONS = 1000

# ----------------------------------------------------------------------
# ICA Parameters
# ----------------------------------------------------------------------
ICA_N_COMPONENTS = 20  # Default, can be overridden
ICA_MAX_ITER = 1000

# ----------------------------------------------------------------------
# Preprocessing Parameters
# ----------------------------------------------------------------------
FILTER_BAND = (1, 40)  # Hz
MIN_VALID_DURATION_SECONDS = 240  # 4 minutes

# ----------------------------------------------------------------------
# Microstate Parameters
# ----------------------------------------------------------------------
N_MICROSTATES = 4  # Canonical A, B, C, D

# ----------------------------------------------------------------------
# Spectral Power Bands (Hz)
# ----------------------------------------------------------------------
SPECTRAL_BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "low_gamma": (30, 45),
    "high_gamma": (45, 60),
}

# ----------------------------------------------------------------------
# Model Parameters
# ----------------------------------------------------------------------
ELASTIC_NET_ALPHA = 0.5
ELASTIC_NET_L1_RATIO = 0.5

# ----------------------------------------------------------------------
# Diagnostics
# ----------------------------------------------------------------------
VIF_THRESHOLD = 10.0
FDR_METHOD = "fdr_bh"  # Benjamini-Hochberg

# ----------------------------------------------------------------------
# OpenNeuro Dataset ID (can be overridden via env var)
# ----------------------------------------------------------------------
OPENNEURO_DATASET_ID = os.getenv("OPENNEURO_DATASET_ID", "ds003XXX")

# ----------------------------------------------------------------------
# Exported legacy constants expected by downstream code & tests
# ----------------------------------------------------------------------
RAW_DIR = DATA_RAW_DIR
PROCESSED_DIR = DATA_PROCESSED_DIR
# ARTIFACTS_DIR already defined above; re‑export for clarity
# Expected feature column order (30 features)
EXPECTED_FEATURE_COLUMNS = [
    # Mean Durations
    "duration_A",
    "duration_B",
    "duration_C",
    "duration_D",
    # Occurrence Rates
    "occurrence_A",
    "occurrence_B",
    "occurrence_C",
    "occurrence_D",
    # Transition Probabilities (4 x 4 matrix flattened)
    "trans_AA",
    "trans_AB",
    "trans_AC",
    "trans_AD",
    "trans_BA",
    "trans_BB",
    "trans_BC",
    "trans_BD",
    "trans_CA",
    "trans_CB",
    "trans_CC",
    "trans_CD",
    "trans_DA",
    "trans_DB",
    "trans_DC",
    "trans_DD",
    # Spectral Power Features
    "power_delta",
    "power_theta",
    "power_alpha",
    "power_beta",
    "power_low_gamma",
    "power_high_gamma",
]

# ----------------------------------------------------------------------
# Helper functions for path resolution and environment variables
# ----------------------------------------------------------------------
def get_path(subpath: Optional[str] = None) -> Path:
    """
    Return the absolute project root, optionally appended with a sub‑path.

    Parameters
    ----------
    subpath : str, optional
        Relative path to append to the project root.

    Returns
    -------
    Path
        The resolved absolute path.
    """
    if subpath:
        return _PROJECT_ROOT / subpath
    return _PROJECT_ROOT

def get_dir(key: str) -> Path:
    """
    Resolve a logical directory key to its absolute path.

    Parameters
    ----------
    key : str
        One of the keys defined in ``_DIRS`` (e.g., "raw", "processed").

    Returns
    -------
    Path
        Absolute path to the requested directory.

    Raises
    ------
    KeyError
        If ``key`` is not present in ``_DIRS``.
    """
    if key not in _DIRS:
        raise KeyError(f"Directory key not recognized: {key}")
    return _PROJECT_ROOT / _DIRS[key]

def get_seed() -> int:
    """
    Retrieve the random seed from the environment variable ``LLMXIVE_SEED``.
    Falls back to ``DEFAULT_SEED`` when the variable is absent or invalid.
    """
    seed_str = os.getenv("LLMXIVE_SEED")
    if seed_str and seed_str.isdigit():
        return int(seed_str)
    return DEFAULT_SEED

def get_max_iter() -> int:
    """
    Retrieve the maximum iteration count from ``LLMXIVE_MAX_ITER``.
    Falls back to ``DEFAULT_MAX_ITER`` when unset or invalid.
    """
    max_iter_str = os.getenv("LLMXIVE_MAX_ITER")
    if max_iter_str and max_iter_str.isdigit():
        return int(max_iter_str)
    return DEFAULT_MAX_ITER

def get_log_level() -> str:
    """
    Retrieve the desired logging level from ``LLMXIVE_LOG_LEVEL``.
    Defaults to ``"INFO"`` if not set.
    """
    return os.getenv("LLMXIVE_LOG_LEVEL", "INFO")

# ----------------------------------------------------------------------
# Directory creation / validation utilities
# ----------------------------------------------------------------------
def ensure_directories() -> None:
    """
    Create all required project directories if they do not exist.
    Safe to call multiple times (idempotent).
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        ARTIFACTS_DIR,
        STATE_DIR / "projects",
        CODE_DIR,
        TESTS_DIR,
        SPECS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def validate_paths() -> bool:
    """
    Validate that critical directories exist. Calls ``ensure_directories``
    to guarantee their presence and then returns a boolean indicating
    success.
    """
    ensure_directories()
    return (
        DATA_RAW_DIR.exists()
        and DATA_PROCESSED_DIR.exists()
        and ARTIFACTS_DIR.exists()
        and STATE_DIR.exists()
    )

# ----------------------------------------------------------------------
# When run as a script, print a summary of configuration values.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import json

    config_summary = {
        "project_root": str(_PROJECT_ROOT),
        "raw_dir": str(RAW_DIR),
        "processed_dir": str(PROCESSED_DIR),
        "artifacts_dir": str(ARTIFACTS_DIR),
        "max_execution_hours": MAX_EXECUTION_HOURS,
        "default_seed": DEFAULT_SEED,
        "openneuro_dataset_id": OPENNEURO_DATASET_ID,
    }
    print(json.dumps(config_summary, indent=2))
    # Also validate that required directories are present.
    validate_paths()