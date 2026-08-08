"""
Project Configuration and Path Resolution.

Provides helper functions to resolve project directories relative to the
repository root.
"""
import os
from pathlib import Path

# Determine the project root. 
# We assume this file is in code/config.py, so root is 2 levels up.
# If run as a module, we might need to adjust.
# For safety, we look for a marker file or assume the structure.
# Standard assumption: project_root = Path(__file__).parent.parent
_PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    """Return the path to the data directory."""
    return get_project_root() / "data"

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
