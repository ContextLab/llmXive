import os
from pathlib import Path

def get_project_root():
    """
    Returns the absolute path to the project root directory.
    Assumes the script is run from the project root or that this file is inside 'code/'.
    """
    # If running from code/, go up one level. If running from root, stay.
    current_file = Path(__file__).resolve()
    parent = current_file.parent
    
    # Heuristic: If 'code' is the immediate parent of this file, root is parent's parent
    if parent.name == 'code':
        return parent.parent
    return parent

def get_data_dir():
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_raw_data_dir():
    """Returns the path to the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_data_dir():
    """Returns the path to the processed data directory."""
    return get_data_dir() / "processed"

def get_consent_dir():
    """Returns the path to the consent records directory."""
    return get_data_dir() / "consent"

def get_specs_dir():
    """Returns the path to the specs directory."""
    return get_project_root() / "specs"

def get_contracts_dir():
    """Returns the path to the contracts directory."""
    return get_specs_dir() / "001-text-tone-emotional-support" / "contracts"

def get_figures_dir():
    """Returns the path to the figures directory."""
    return get_project_root() / "figures"

def get_code_dir():
    """Returns the path to the code directory."""
    return get_project_root() / "code"

def get_tests_dir():
    """Returns the path to the tests directory."""
    return get_project_root() / "tests"