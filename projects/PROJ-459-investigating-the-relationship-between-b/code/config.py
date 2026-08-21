"""
Configuration management for the Brain-Music Preference pipeline.
Handles paths, hyperparameters, dataset IDs, and environment constraints.
"""
import os
import json
import resource
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Structure
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

# Dataset Configuration
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

# Hyperparameters
HYPERPARAMETERS = {
    "window_sizes": [20, 30, 40],  # TRs
    "step_size": 5,  # TRs
    "fmriprep_args": [
        "--output-space",
        "MNI152NLin2009cAsym",
        "--confounds",
        "trans_x,trans_y,trans_z,rot_x,rot_y,rot_z,framewise_displacement,dvars",
    ],
    "fd_threshold": 0.5,  # mm
    "missing_data_threshold": 0.1,  # 10%
    "min_sample_size": 85,  # Power requirement override
    "permutations": 1000,  # Null validation requirement override
}

# Environment Constraints
ENV_CONSTRAINTS = {
    "memory_limit_gb": 16.0,  # Soft limit for fMRIPrep
    "runtime_limit_hours": 6.0,
    "warning_threshold": 0.8,  # Warn at 80% of limit
}


def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)


def get_data_path(dataset_id: str, filename: Optional[str] = None) -> Path:
    """
    Construct a path to raw data.

    Args:
        dataset_id: The dataset identifier (e.g., 'ds000030').
        filename: Optional filename to append.

    Returns:
        Path object pointing to the data location.
    """
    base = DIRS["data_raw"] / dataset_id
    if filename:
        return base / filename
    return base


def get_processed_path(subject_id: str, filename: Optional[str] = None) -> Path:
    """
    Construct a path to processed data for a specific subject.

    Args:
        subject_id: The subject identifier.
        filename: Optional filename to append.

    Returns:
        Path object pointing to the processed location.
    """
    base = DIRS["data_processed"] / subject_id
    if filename:
        return base / filename
    return base


def get_derived_path(filename: str) -> Path:
    """
    Construct a path to derived data (aggregates, reports).

    Args:
        filename: The filename.

    Returns:
        Path object pointing to the derived location.
    """
    return DIRS["data_derived"] / filename


def get_figure_path(filename: str) -> Path:
    """
    Construct a path to a figure.

    Args:
        filename: The filename.

    Returns:
        Path object pointing to the figures location.
    """
    return DIRS["figures"] / filename


def get_env_config() -> Dict[str, Any]:
    """
    Retrieve the current environment configuration.

    Returns:
        Dictionary containing memory limits and runtime constraints.
    """
    return ENV_CONSTRAINTS


def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, float]:
    """
    Verify available RAM against a specified or configured limit.

    This function checks the soft memory limit of the current process
    (or the system if the process limit is unlimited) to ensure sufficient
    resources for fMRIPrep execution.

    Args:
        limit_gb: Optional override for the memory limit in GB.
                  Defaults to ENV_CONSTRAINTS['memory_limit_gb'].

    Returns:
        Tuple of (is_sufficient: bool, available_gb: float).
        If is_sufficient is False, the available memory is below the limit.
    """
    if limit_gb is None:
        limit_gb = ENV_CONSTRAINTS["memory_limit_gb"]

    # Get soft limit in bytes (0 means unlimited)
    soft_limit, _ = resource.getrlimit(resource.RLIMIT_AS)

    if soft_limit == 0:
        # If unlimited, try to estimate system memory or assume safe
        # Fallback to a conservative estimate if /proc/meminfo is not available
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        # Parse "MemTotal:       16384000 kB"
                        parts = line.split()
                        mem_kb = int(parts[1])
                        available_gb = mem_kb / (1024 * 1024)
                        break
                else:
                    # Fallback if parsing fails
                    available_gb = 32.0
        except (FileNotFoundError, ValueError):
            # Fallback for non-Linux or unreadable files
            available_gb = 32.0
    else:
        available_gb = soft_limit / (1024 * 1024 * 1024)

    is_sufficient = available_gb >= limit_gb
    return is_sufficient, available_gb


def set_runtime_cap(hours: Optional[float] = None) -> None:
    """
    Set a soft runtime limit for the current process.

    This is a warning mechanism. If the process exceeds this time,
    the OS may send a SIGXCPU signal (though Python doesn't catch it by default
    without a handler). This function primarily serves as a configuration
    setter for monitoring tools or external watchdogs.

    Args:
        hours: The time limit in hours. Defaults to ENV_CONSTRAINTS['runtime_limit_hours'].
    """
    if hours is None:
        hours = ENV_CONSTRAINTS["runtime_limit_hours"]

    seconds = int(hours * 3600)
    # Set soft limit (SIGXCPU) and hard limit
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))

def get_data_path(dataset_id: str, filename: Optional[str] = None) -> Path:
    """
    Construct a path to raw data.

    Args:
        dataset_id: The dataset identifier (e.g., 'ds000030').
        filename: Optional filename to append.

    Returns:
        Path object pointing to the data location.
    """
    base = DIRS["data_raw"] / dataset_id
    if filename:
        return base / filename
    return base


def get_processed_path(subject_id: str, filename: Optional[str] = None) -> Path:
    """
    Construct a path to processed data for a specific subject.

    Args:
        subject_id: The subject identifier.
        filename: Optional filename to append.

    Returns:
        Path object pointing to the processed location.
    """
    base = DIRS["data_processed"] / subject_id
    if filename:
        return base / filename
    return base


def get_derived_path(filename: str) -> Path:
    """
    Construct a path to derived data (aggregates, reports).

    Args:
        filename: The filename.

    Returns:
        Path object pointing to the derived location.
    """
    return DIRS["data_derived"] / filename


def get_figure_path(filename: str) -> Path:
    """
    Construct a path to a figure.

    Args:
        filename: The filename.

    Returns:
        Path object pointing to the figures location.
    """
    return DIRS["figures"] / filename


def get_env_config() -> Dict[str, Any]:
    """
    Retrieve the current environment configuration.

    Returns:
        Dictionary containing memory limits and runtime constraints.
    """
    return ENV_CONSTRAINTS


def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, float]:
    """
    Verify available RAM against a specified or configured limit.

    This function checks the soft memory limit of the current process
    (or the system if the process limit is unlimited) to ensure sufficient
    resources for fMRIPrep execution.

    Args:
        limit_gb: Optional override for the memory limit in GB.
                  Defaults to ENV_CONSTRAINTS['memory_limit_gb'].

    Returns:
        Tuple of (is_sufficient: bool, available_gb: float).
        If is_sufficient is False, the available memory is below the limit.
    """
    if limit_gb is None:
        limit_gb = ENV_CONSTRAINTS["memory_limit_gb"]

    # Get soft limit in bytes (0 means unlimited)
    soft_limit, _ = resource.getrlimit(resource.RLIMIT_AS)

    if soft_limit == 0:
        # If unlimited, try to estimate system memory or assume safe
        # Fallback to a conservative estimate if /proc/meminfo is not available
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        # Parse "MemTotal:       16384000 kB"
                        parts = line.split()
                        mem_kb = int(parts[1])
                        available_gb = mem_kb / (1024 * 1024)
                        break
                else:
                    # Fallback if parsing fails
                    available_gb = 32.0
        except (FileNotFoundError, ValueError):
            # Fallback for non-Linux or unreadable files
            available_gb = 32.0
    else:
        available_gb = soft_limit / (1024 * 1024 * 1024)

    is_sufficient = available_gb >= limit_gb
    return is_sufficient, available_gb


def set_runtime_cap(hours: Optional[float] = None) -> None:
    """
    Set a soft runtime limit for the current process.

    This is a warning mechanism. If the process exceeds this time,
    the OS may send a SIGXCPU signal (though Python doesn't catch it by default
    without a handler). This function primarily serves as a configuration
    setter for monitoring tools or external watchdogs.

    Args:
        hours: The time limit in hours. Defaults to ENV_CONSTRAINTS['runtime_limit_hours'].
    """
    if hours is None:
        hours = ENV_CONSTRAINTS["runtime_limit_hours"]

    seconds = int(hours * 3600)
    # Set soft limit (SIGXCPU) and hard limit
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))

def get_data_path(dataset_id: str, filename: Optional[str] = None) -> Path:
    """
    Construct a path to raw data.

    Args:
        dataset_id: The dataset identifier (e.g., 'ds000030').
        filename: Optional filename to append.

    Returns:
        Path object pointing to the data location.
    """
    base = DIRS["data_raw"] / dataset_id
    if filename:
        return base / filename
    return base


def get_processed_path(subject_id: str, filename: Optional[str] = None) -> Path:
    """
    Construct a path to processed data for a specific subject.

    Args:
        subject_id: The subject identifier.
        filename: Optional filename to append.

    Returns:
        Path object pointing to the processed location.
    """
    base = DIRS["data_processed"] / subject_id
    if filename:
        return base / filename
    return base


def get_derived_path(filename: str) -> Path:
    """
    Construct a path to derived data (aggregates, reports).

    Args:
        filename: The filename.

    Returns:
        Path object pointing to the derived location.
    """
    return DIRS["data_derived"] / filename


def get_figure_path(filename: str) -> Path:
    """
    Construct a path to a figure.

    Args:
        filename: The filename.

    Returns:
        Path object pointing to the figures location.
    """
    return DIRS["figures"] / filename


def get_env_config() -> Dict[str, Any]:
    """
    Retrieve the current environment configuration.

    Returns:
        Dictionary containing memory limits and runtime constraints.
    """
    return ENV_CONSTRAINTS


def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, float]:
    """
    Verify available RAM against a specified or configured limit.

    This function checks the soft memory limit of the current process
    (or the system if the process limit is unlimited) to ensure sufficient
    resources for fMRIPrep execution.

    Args:
        limit_gb: Optional override for the memory limit in GB.
                  Defaults to ENV_CONSTRAINTS['memory_limit_gb'].

    Returns:
        Tuple of (is_sufficient: bool, available_gb: float).
        If is_sufficient is False, the available memory is below the limit.
    """
    if limit_gb is None:
        limit_gb = ENV_CONSTRAINTS["memory_limit_gb"]

    # Get soft limit in bytes (0 means unlimited)
    soft_limit, _ = resource.getrlimit(resource.RLIMIT_AS)

    if soft_limit == 0:
        # If unlimited, try to estimate system memory or assume safe
        # Fallback to a conservative estimate if /proc/meminfo is not available
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        # Parse "MemTotal:       16384000 kB"
                        parts = line.split()
                        mem_kb = int(parts[1])
                        available_gb = mem_kb / (1024 * 1024)
                        break
                else:
                    # Fallback if parsing fails
                    available_gb = 32.0
        except (FileNotFoundError, ValueError):
            # Fallback for non-Linux or unreadable files
            available_gb = 32.0
    else:
        available_gb = soft_limit / (1024 * 1024 * 1024)

    is_sufficient = available_gb >= limit_gb
    return is_sufficient, available_gb


def set_runtime_cap(hours: Optional[float] = None) -> None:
    """
    Set a soft runtime limit for the current process.

    This is a warning mechanism. If the process exceeds this time,
    the OS may send a SIGXCPU signal (though Python doesn't catch it by default
    without a handler). This function primarily serves as a configuration
    setter for monitoring tools or external watchdogs.

    Args:
        hours: The time limit in hours. Defaults to ENV_CONSTRAINTS['runtime_limit_hours'].
    """
    if hours is None:
        hours = ENV_CONSTRAINTS["runtime_limit_hours"]

    seconds = int(hours * 3600)
    # Set soft limit (SIGXCPU) and hard limit
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
