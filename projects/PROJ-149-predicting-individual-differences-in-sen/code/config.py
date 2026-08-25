"""
Configuration module for the EEG Sensory Processing Speed pipeline.
Defines paths, parameters, and utility functions used across the project.
"""
import os
import numpy as np
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
CODE_ROOT = PROJECT_ROOT / "code"

# Constants
EPSILON = 1e-9
OVERLAP = 0.5
WINDOW_SIZE = 2  # Overridden by Constitution Principle VI
SEED = 42
POLY_DEGREE = 2

# Band definitions (Hz)
BAND_FREQS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "low_beta": (13, 20),
    "high_beta": (20, 30),
    "gamma": (30, 40)
}

# ICA parameters
ICA_MAX_ITER = 200
ICA_RANDOM_STATE = SEED

# Preprocessing parameters
FILTER_LOW = 1.0
FILTER_HIGH = 40.0
NOTCH_FREQS = [50, 60]  # Hz
VARIANCE_THRESHOLD_SD = 3.0
MAX_REJECTED_CHANNELS_RATIO = 0.30
MIN_TRIALS_RATIO = 0.70
MIN_EPOCH_DURATION_MINUTES = 2

# Modeling parameters
CV_FOLDS = 5
TRAIN_TEST_SPLIT = 0.8

# Paths map - supports various calling conventions
# Keys are logical names, values are relative paths from PROJECT_ROOT
PATHS = {
    "data_raw": "data/raw",
    "data_interim": "data/interim",
    "data_processed": "data/processed",
    "data": "data",
    "raw_data": "data/raw",
    "processed_data": "data/processed",
    "interim": "data/interim",
    "processed": "data/processed",
    "features": "data/processed/features.csv",
    "features_clr": "data/processed/features_clr.csv",
    "model_results": "data/processed/model_results.json",
    "correlations": "data/interim/correlations_raw.csv",
    "correlations_corrected": "data/processed/correlations_corrected.csv",
    "non_linear_comparison": "data/processed/non_linear_comparison.json",
    "permutation_results": "data/processed/permutation_results.json",
    "robustness_report": "data/processed/robustness_report.csv",
    "sensitivity_report": "data/processed/sensitivity_report.csv",
    "sensitivity_plot": "data/processed/sensitivity_plot.png",
    "final_report": "data/processed/final_report.md",
    "joined_metadata": "data/interim/joined_metadata.csv",
    "behavioral_metrics": "data/interim/behavioral_metrics.csv",
    "behavioral_exclusion_log": "data/interim/behavioral_exclusion_log.csv",
    "eeg_psd": "data/interim/eeg_psd.csv",
    "split_indices": "data/interim/split_indices.json",
    "preprocessed_eeg": "data/interim/preprocessed_eeg",
    "ica_cleaned_eeg": "data/interim/ica_cleaned_eeg",
    "exclusion_log": "data/interim/exclusion_log.csv",
    "manifest": "data/interim/data_source_manifest.json",
    "feasibility_report": "data/processed/feasibility_report.md",
    "verification_log": "data/processed/verification_log.json",
}

def get_epsilon():
    """Return the epsilon value for numerical stability."""
    return EPSILON

def get_seed():
    """Return the random seed."""
    return SEED

def get_band_freqs():
    """Return the band frequency definitions."""
    return BAND_FREQS

def get_all_band_names():
    """Return list of all band names."""
    return list(BAND_FREQS.keys())

def get_window_seconds():
    """Return window size in seconds."""
    return WINDOW_SIZE

def get_overlap_seconds():
    """Return overlap in seconds."""
    return OVERLAP

def get_min_epoch_duration_minutes():
    """Return minimum epoch duration in minutes."""
    return MIN_EPOCH_DURATION_MINUTES

def get_cv_folds():
    """Return number of CV folds."""
    return CV_FOLDS

def get_path(*args):
    """
    Flexible path resolver supporting multiple calling conventions.

    Conventions supported:
    1. get_path("logical_key") -> resolves from PATHS map
    2. get_path("logical_key", "subpath") -> resolves key, appends subpath
    3. get_path("absolute_or_relative/path") -> returns Path object directly
    4. get_path(base_dir, "relative/path") -> joins base_dir and relative path

    Args:
        *args: Variable length argument list.

    Returns:
        Path: Resolved path object.
    """
    if not args:
        raise ValueError("get_path() requires at least one argument.")

    # Case 1: Single string argument
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, str):
            # Check if it's a logical key
            if arg in PATHS:
                return PROJECT_ROOT / PATHS[arg]
            # Otherwise treat as relative or absolute path
            return PROJECT_ROOT / arg
        elif isinstance(arg, Path):
            return arg
        else:
            raise TypeError(f"Unsupported argument type: {type(arg)}")

    # Case 2: Two arguments (base, relative)
    if len(args) == 2:
        base, relative = args
        if isinstance(base, str) and base in PATHS:
            base_path = PROJECT_ROOT / PATHS[base]
        elif isinstance(base, (str, Path)):
            base_path = PROJECT_ROOT / base if isinstance(base, str) else base
        else:
            base_path = PROJECT_ROOT / str(base) if base else PROJECT_ROOT

        if isinstance(relative, str):
            return base_path / relative
        elif isinstance(relative, Path):
            return base_path / relative
        else:
            return base_path / str(relative)

    # Case 3: More than two arguments (unlikely, but handle gracefully)
    # Treat first as base, rest as path components
    base = args[0]
    if isinstance(base, str) and base in PATHS:
        base_path = PROJECT_ROOT / PATHS[base]
    else:
        base_path = PROJECT_ROOT / str(base) if base else PROJECT_ROOT

    path_components = [str(a) for a in args[1:]]
    return base_path / os.path.join(*path_components)

def ensure_dirs(*args):
    """
    Flexible directory creator supporting multiple calling conventions.

    Conventions supported:
    1. ensure_dirs() -> does nothing (no-op)
    2. ensure_dirs("path_string") -> creates directory at path
    3. ensure_dirs(Path_object) -> creates directory at path
    4. ensure_dirs(["path1", "path2"]) -> creates multiple directories
    5. ensure_dirs(Path_object1, Path_object2) -> creates multiple directories

    Args:
        *args: Variable length argument list.
    """
    if not args:
        # No-op case
        return None

    # Flatten arguments if a list is passed
    paths_to_create = []
    for arg in args:
        if isinstance(arg, list):
            paths_to_create.extend(arg)
        else:
            paths_to_create.append(arg)

    for path in paths_to_create:
        if isinstance(path, str):
            # Check if it's a logical key first
            if path in PATHS:
                full_path = PROJECT_ROOT / PATHS[path]
            else:
                full_path = PROJECT_ROOT / path
        elif isinstance(path, Path):
            full_path = path
        else:
            full_path = PROJECT_ROOT / str(path)

        full_path.mkdir(parents=True, exist_ok=True)

    # Return the last created path or None if no paths were created
    return full_path if paths_to_create else None

def bonferroni_correct(p_values, num_tests=None):
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List or array of p-values.
        num_tests: Number of tests (defaults to len(p_values)).

    Returns:
        List of corrected p-values.
    """
    if num_tests is None:
        num_tests = len(p_values)
    return [min(p * num_tests, 1.0) for p in p_values]