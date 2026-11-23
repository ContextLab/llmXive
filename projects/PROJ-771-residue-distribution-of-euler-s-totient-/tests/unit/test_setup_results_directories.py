"""
Unit tests for setup_results_directories.py.
Verifies that the results directory structure is created correctly.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# We need to adjust the import path since we are running from tests/unit
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_results_directories import setup_results_directories

def test_setup_results_directories_creates_folders():
    """Test that the function creates the required directories."""
    # We test in a temporary directory to avoid polluting the real repo during test
    # However, the function uses __file__ to determine the root. 
    # To properly test this in isolation, we would need to refactor the function
    # to accept a root path. For now, we verify the logic by checking the 
    # expected behavior relative to the project structure.
    
    # Since the function relies on the actual file location, we assume
    # the test is run within the context of the project structure.
    # We verify that the directories exist relative to the code directory.
    
    code_dir = Path(__file__).resolve().parent.parent.parent / "code"
    # The function calculates root as parent of code dir
    expected_root = code_dir.parent
    expected_plots = expected_root / "results" / "plots"
    expected_reports = expected_root / "results" / "reports"

    # Run the setup
    setup_results_directories()

    # Assert directories exist
    assert expected_plots.exists(), f"Directory {expected_plots} was not created."
    assert expected_reports.exists(), f"Directory {expected_reports} was not created."
    assert expected_plots.is_dir(), f"{expected_plots} is not a directory."
    assert expected_reports.is_dir(), f"{expected_reports} is not a directory."