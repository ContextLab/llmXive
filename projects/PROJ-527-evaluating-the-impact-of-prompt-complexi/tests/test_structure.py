"""
Tests for Project Structure Initialization.

Verifies that the required directories exist after running the setup script.
"""

import os
import pytest
from pathlib import Path

# Import the setup function if needed, though we mostly test filesystem state
# We assume the setup script has already been run or will be run in a fixture
# For this task, we verify the expected structure exists.

@pytest.fixture
def project_root():
    """Return the project root path."""
    return Path(__file__).parent.parent

def test_code_directory_exists(project_root):
    """Verify the code directory exists."""
    assert (project_root / "code").is_dir(), "Directory 'code' does not exist"

def test_tests_directory_exists(project_root):
    """Verify the tests directory exists."""
    assert (project_root / "tests").is_dir(), "Directory 'tests' does not exist"

def test_data_raw_directory_exists(project_root):
    """Verify the data/raw directory exists."""
    assert (project_root / "data" / "raw").is_dir(), "Directory 'data/raw' does not exist"

def test_data_processed_directory_exists(project_root):
    """Verify the data/processed directory exists."""
    assert (project_root / "data" / "processed").is_dir(), "Directory 'data/processed' does not exist"

def test_data_results_directory_exists(project_root):
    """Verify the data/results directory exists."""
    assert (project_root / "data" / "results").is_dir(), "Directory 'data/results' does not exist"

def test_state_directory_exists(project_root):
    """Verify the state directory exists."""
    assert (project_root / "state").is_dir(), "Directory 'state' does not exist"