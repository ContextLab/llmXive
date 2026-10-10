"""
Configuration management for the Brain-Music Preference pipeline.
Handles paths, hyperparameters, dataset IDs, and environment constraints.
Includes a simple mechanism to switch the active dataset if validation fails.
"""
import os
import json
import resource
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# ----------------------------------------------------------------------
# Project root and directory layout
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRS = {
    "code": PROJECT_ROOT / "code",
    "tests": PROJECT_ROOT / "tests",
    "data": PROJECT_ROOT / "data",
    "state": PROJECT_ROOT / "state",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_derived": PROJECT_ROOT / "data" / "derived",
    "figures": PROJECT_ROOT / "figures",
    "state_projects": PROJECT_ROOT / "state" / "projects",
}

# ----------------------------------------------------------------------
# Dataset configuration
# ----------------------------------------------------------------------
DATASET_CONFIG = {
    "ds000030": {
        "id": "ds000030",
        "name": "OpenNeuro ds000030",
        "url": "https://openneuro.org/datasets/ds000030",
        "type": "resting_state",
        "active": True,
    },
    "ds000208": {
        "id": "ds000208",
        "name": "OpenNeuro ds000208",
        "url": "https://openneuro.org/datasets/ds000208",
        "type": "resting_state",
        "active": True,
    },
}

# Default active dataset – can be overridden by environment variable
_CURRENT_DATASET_ID: str = os.getenv("DATASET_ID") or next(
    (cfg["id"] for cfg in DATASET_CONFIG.values() if cfg["active"]),
    list(DATASET_CONFIG.keys())[0],
)

# ----------------------------------------------------------------------
# Hyperparameters
# ----------------------------------------------------------------------
HYPERPARAMETERS = {
    "window_sizes": [20, 30, 40],  # TRs
    "step_size": 5,                # TRs
    "fmriprep_args": [
        "--output-space",
        "MNI152NLin2009cAsym",
        "--confounds",
        "trans_x,trans_y,trans_z,rot_x,rot_y,rot_z,framewise_displacement,dvars",
    ],
    "fd_threshold": 0.5,               # mm
    "missing_data_threshold": 0.1,      # 10%
    "min_sample_size": 85,              # Power requirement
    "permutations": 1000,               # Null‑distribution permutations
}

# ----------------------------------------------------------------------
# Environment constraints
# ----------------------------------------------------------------------
ENV_CONSTRAINTS = {
    "memory_limit_gb": 16.0,   # Soft limit for fMRIPrep
    "runtime_limit_hours": 6.0,
    "warning_threshold": 0.8, # Warn at 80 % of limit
}

# ----------------------------------------------------------------------
# Directory helpers
# ----------------------------------------------------------------------
def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)

def get_data_path(dataset_id: Optional[str] = None, filename: Optional[str] = None) -> Path:
    """
    Construct a path to raw data.

    If ``dataset_id`` is ``None`` the base raw‑data directory is returned.
    """
    base = DIRS["data_raw"]
    if dataset_id:
        base = base / dataset_id
    if filename:
        return base / filename
    return base

def get_processed_path(subject_id: str, filename: Optional[str] = None) -> Path:
    """
    Construct a path to processed data for a specific subject.
    """
    base = DIRS["data_processed"] / subject_id
    if filename:
        return base / filename
    return base

def get_derived_path(filename: str) -> Path:
    """
    Construct a path to derived data (aggregates, reports).
    """
    return DIRS["data_derived"] / filename

def get_figure_path(filename: str) -> Path:
    """
    Construct a path to a figure.
    """
    return DIRS["figures"] / filename

def get_env_config() -> Dict[str, Any]:
    """Return the environment‑constraint dictionary."""
    return ENV_CONSTRAINTS.copy()

# ----------------------------------------------------------------------
# Memory‑limit helper
# ----------------------------------------------------------------------
def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, float]:
    """
    Verify available RAM against a specified or configured limit.

    Returns (is_sufficient, available_gb).
    """
    if limit_gb is None:
        limit_gb = ENV_CONSTRAINTS["memory_limit_gb"]

    soft_limit, _ = resource.getrlimit(resource.RLIMIT_AS)

    if soft_limit == 0:
        # Unlimited – try to read /proc/meminfo on Linux
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        parts = line.split()
                        mem_kb = int(parts[1])
                        available_gb = mem_kb / (1024 * 1024)
                        break
                else:
                    available_gb = 32.0
        except (FileNotFoundError, ValueError):
            available_gb = 32.0
    else:
        available_gb = soft_limit / (1024 * 1024 * 1024)

    return available_gb >= limit_gb, available_gb

# ----------------------------------------------------------------------
# Runtime‑cap helper
# ----------------------------------------------------------------------
def set_runtime_cap(hours: Optional[float] = None) -> None:
    """
    Set a soft CPU‑time limit (SIGXCPU). This is only a warning mechanism.
    """
    if hours is None:
        hours = ENV_CONSTRAINTS["runtime_limit_hours"]
    seconds = int(hours * 3600)
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))

# ----------------------------------------------------------------------
# Dataset‑selection utilities
# ----------------------------------------------------------------------
def get_active_dataset_id() -> str:
    """
    Return the currently selected dataset identifier.
    """
    return _CURRENT_DATASET_ID

def set_active_dataset_id(new_id: str) -> None:
    """
    Switch the active dataset to ``new_id`` if it exists in ``DATASET_CONFIG``.
    Raises ``KeyError`` if the identifier is unknown.
    """
    global _CURRENT_DATASET_ID
    if new_id not in DATASET_CONFIG:
        raise KeyError(f"Dataset ID '{new_id}' is not configured.")
    _CURRENT_DATASET_ID = new_id

def switch_dataset_on_failure(failed_id: str) -> str:
    """
    If validation of ``failed_id`` fails, automatically pick an alternative
    active dataset. Returns the newly selected dataset ID.

    The simple strategy is:
    1. Mark the failed dataset as inactive.
    2. Return the first remaining active dataset.
    3. If none remain, raise ``RuntimeError``.
    """
    if failed_id in DATASET_CONFIG:
        DATASET_CONFIG[failed_id]["active"] = False
    # Find first still‑active dataset
    for cfg in DATASET_CONFIG.values():
        if cfg.get("active"):
            set_active_dataset_id(cfg["id"])
            return cfg["id"]
    raise RuntimeError("No active datasets remain after failure.")

# ----------------------------------------------------------------------
# Convenience wrappers used throughout the pipeline
# ----------------------------------------------------------------------
def data_path(*, filename: Optional[str] = None) -> Path:
    """
    Shortcut for ``get_data_path`` using the currently active dataset.
    """
    return get_data_path(_CURRENT_DATASET_ID, filename)

# The module's public interface
__all__ = [
    "ensure_dirs",
    "get_data_path",
    "get_processed_path",
    "get_derived_path",
    "get_figure_path",
    "get_env_config",
    "check_memory_limit",
    "set_runtime_cap",
    "get_active_dataset_id",
    "set_active_dataset_id",
    "switch_dataset_on_failure",
    "data_path",
    "HYPERPARAMETERS",
    "DATASET_CONFIG",
]
