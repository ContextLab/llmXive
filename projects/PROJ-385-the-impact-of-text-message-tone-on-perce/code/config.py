"""
Configuration management for the project.
Handles path resolution and random seed pinning.
"""
import os
from pathlib import Path

# Random seed for reproducibility
RANDOM_SEED = 42

# Project root resolution
def get_project_root() -> Path:
    """Returns the absolute path to the project root directory."""
    # Assuming the code is run from the project root or code/ subdirectory
    # We look for the 'data' directory to anchor the root.
    current = Path(__file__).resolve()
    # Traverse up until we find 'data' or 'specs' or reach root
    while current != current.parent:
        if (current / "data").exists() or (current / "specs").exists():
            return current
        current = current.parent
    # Fallback to parent of code/
    return current.parent

# Path constants
DATA_ROOT = get_project_root() / "data"
STIMULI_PATH = DATA_ROOT / "raw" / "stimuli.csv"
RATINGS_PATH = DATA_ROOT / "raw" / "ratings.csv"
POWER_ANALYSIS_RESULTS_PATH = DATA_ROOT / "processed" / "power_analysis_results.json"
CLEANING_LOG_PATH = DATA_ROOT / "processed" / "cleaning_log.csv"
ANALYSIS_RESULTS_PATH = DATA_ROOT / "processed" / "analysis_results.json"
SENSITIVITY_DEFINITIONS_PATH = DATA_ROOT / "processed" / "sensitivity_definitions.json"
SENSITIVITY_REPORT_PATH = DATA_ROOT / "processed" / "sensitivity_report.csv"
PIPELINE_LOG_PATH = DATA_ROOT / "pipeline.log"

# Directory path helpers
def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_raw_data_dir() -> Path:
    """Returns the path to the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_data_dir() -> Path:
    """Returns the path to the processed data directory."""
    return get_data_dir() / "processed"

def get_consent_dir() -> Path:
    """Returns the path to the consent records directory."""
    return get_data_dir() / "consent"

def get_specs_dir() -> Path:
    """Returns the path to the specs directory."""
    return get_project_root() / "specs"

def get_contracts_dir() -> Path:
    """Returns the path to the contracts directory."""
    return get_specs_dir() / "001-text-tone-emotional-support" / "contracts"

def get_figures_dir() -> Path:
    """Returns the path to the figures directory."""
    return get_data_dir() / "figures"

def get_code_dir() -> Path:
    """Returns the path to the code directory."""
    return get_project_root() / "code"

def get_tests_dir() -> Path:
    """Returns the path to the tests directory."""
    return get_project_root() / "tests"