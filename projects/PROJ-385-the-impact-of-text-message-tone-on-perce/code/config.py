import os
from pathlib import Path

# Cache the project root to avoid recomputing it
_PROJECT_ROOT = None

def get_project_root():
    """
    Returns the absolute path to the project root directory.
    Assumes the project root is two levels up from this file's location
    (e.g., code/../..).
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        current_file = Path(__file__).resolve()
        # Assuming structure: code/config.py -> project root is parent of 'code'
        _PROJECT_ROOT = current_file.parent.parent
    return _PROJECT_ROOT

def get_code_dir():
    """Returns the path to the code/ directory."""
    return get_project_root() / "code"

def get_data_dir():
    """Returns the path to the data/ directory."""
    return get_project_root() / "data"

def get_raw_data_dir():
    """Returns the path to data/raw/."""
    return get_data_dir() / "raw"

def get_processed_data_dir():
    """Returns the path to data/processed/."""
    return get_data_dir() / "processed"

def get_consent_dir():
    """Returns the path to data/consent/."""
    return get_data_dir() / "consent"

def get_results_dir():
    """Returns the path to data/results/."""
    return get_data_dir() / "results"

def get_figures_dir():
    """Returns the path to data/figures/."""
    return get_data_dir() / "figures"

def get_specs_dir():
    """Returns the path to specs/ directory."""
    return get_project_root() / "specs"

def get_contracts_dir():
    """Returns the path to specs/.../contracts/ directory."""
    # Assuming contracts are inside the specific spec folder
    spec_folder = get_specs_dir() / "001-the-impact-of-text-message-tone-on-perce"
    return spec_folder / "contracts"

def get_tests_dir():
    """Returns the path to tests/ directory."""
    return get_project_root() / "tests"

def get_mock_data_dir():
    """Returns the path to data/mock/."""
    return get_data_dir() / "mock"

def get_validation_dir():
    """Returns the path to data/validation/."""
    return get_data_dir() / "validation"

# --- Task T007: Configuration Management ---

# Deterministic random seed for all random operations in the pipeline
RANDOM_SEED = 42

# Base data path constant (points to the data/ directory)
BASE_DATA_PATH = get_data_dir()

# Verify constraints immediately upon import to ensure configuration integrity
if not isinstance(RANDOM_SEED, int):
    raise TypeError(f"RANDOM_SEED must be an integer, got {type(RANDOM_SEED)}")

if not BASE_DATA_PATH.is_dir():
    raise FileNotFoundError(f"BASE_DATA_PATH must point to an existing directory, but {BASE_DATA_PATH} does not exist. Ensure data/ directory is created (T001/T005).")

if BASE_DATA_PATH.name != "data":
    raise ValueError(f"BASE_DATA_PATH must point to the 'data' directory, but got {BASE_DATA_PATH}")

# Export for external usage
__all__ = [
    "get_project_root", "get_code_dir", "get_data_dir", "get_raw_data_dir",
    "get_processed_data_dir", "get_consent_dir", "get_results_dir",
    "get_figures_dir", "get_specs_dir", "get_contracts_dir", "get_tests_dir",
    "get_mock_data_dir", "get_validation_dir", "RANDOM_SEED", "BASE_DATA_PATH"
]