"""
Project Configuration and Path Resolution.

Provides helper functions to resolve project directories relative to the
repository root and defines global constants for reproducibility.
"""
import os
from pathlib import Path

# --- Configuration Constants ---
# Fixed random seed for reproducibility across the entire pipeline.
# This must be an integer constant.
RANDOM_SEED: int = 42

# Base data path relative to project root
BASE_DATA_PATH_STR: str = "data"

# --- Path Resolution ---
# Determine the project root.
# We assume this file is in code/config.py, so root is 2 levels up.
_PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    """Return the path to the data directory."""
    # Asserts that BASE_DATA_PATH points to 'data' relative to root
    assert BASE_DATA_PATH_STR == "data", f"BASE_DATA_PATH must point to 'data', got '{BASE_DATA_PATH_STR}'"
    return get_project_root() / BASE_DATA_PATH_STR

def get_raw_data_dir() -> Path:
    """Return the path to the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_data_dir() -> Path:
    """Return the path to the processed data directory."""
    return get_data_dir() / "processed"

def get_consent_dir() -> Path:
    """Return the path to the consent directory."""
    return get_data_dir() / "consent"

def get_results_dir() -> Path:
    """Return the path to the results directory."""
    return get_data_dir() / "results"

def get_specs_dir() -> Path:
    """Return the path to the specs directory."""
    return get_project_root() / "specs" / "001-the-impact-of-text-message-tone-on-perce"

def get_contracts_dir() -> Path:
    """Return the path to the contracts directory."""
    return get_specs_dir() / "contracts"

def get_figures_dir() -> Path:
    """Return the path to the figures directory."""
    return get_data_dir() / "figures"

def get_code_dir() -> Path:
    """Return the path to the code directory."""
    return get_project_root() / "code"

def get_tests_dir() -> Path:
    """Return the path to the tests directory."""
    return get_project_root() / "tests"
