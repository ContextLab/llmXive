"""
Unit tests for the directory setup script (T001).

This test verifies that the expected directory structure is created 
or confirmed to exist after running the setup script.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the main logic from the setup script
# We need to adjust the import path if running as a module, 
# but for this test we will simulate the logic or import the function if refactored.
# For now, we will test the expected behavior by checking the filesystem state
# relative to the test file location.

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXPECTED_DIRS = [
    "data/raw",
    "data/processed",
    "data/artifacts",
    "tests",
    "specs/001-predicting-solubility-in-mixed-solvents/contracts",
]


def test_directory_structure_exists():
    """
    Verify that the required project directories exist.
    
    This test assumes that code/setup_directories.py has been executed 
    or that the directories were created manually.
    """
    missing_dirs = []
    for dir_path in EXPECTED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_path} (is not a directory)")

    assert len(missing_dirs) == 0, f"The following directories are missing: {missing_dirs}"

def test_nested_contract_directory_exists():
    """
    Specifically verify the nested contracts directory structure.
    """
    contracts_path = PROJECT_ROOT / "specs/001-predicting-solubility-in-mixed-solvents/contracts"
    assert contracts_path.exists(), f"Contracts directory missing: {contracts_path}"
    assert contracts_path.is_dir(), f"Contracts path is not a directory: {contracts_path}"