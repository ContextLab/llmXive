"""
Basic smoke test to verify project structure exists.

This test ensures that the directories created by T001a-d and 
initialized by T002 (setup_project.py) are present.
"""
import os
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    """Locate the project root relative to this test file."""
    # test file is at tests/test_setup.py -> root is parent of tests
    return Path(__file__).resolve().parent.parent

def test_code_directory_exists(project_root):
    """Verify T001a: code/ directory exists."""
    code_dir = project_root / "code"
    assert code_dir.exists(), f"Directory 'code' missing at {code_dir}"
    assert code_dir.is_dir(), f"'code' is not a directory"

def test_data_raw_directory_exists(project_root):
    """Verify T001b: data/raw/ directory exists."""
    data_raw = project_root / "data" / "raw"
    assert data_raw.exists(), f"Directory 'data/raw' missing at {data_raw}"
    assert data_raw.is_dir(), f"'data/raw' is not a directory"

def test_data_processed_directory_exists(project_root):
    """Verify T001c: data/processed/ directory exists."""
    data_processed = project_root / "data" / "processed"
    assert data_processed.exists(), f"Directory 'data/processed' missing at {data_processed}"
    assert data_processed.is_dir(), f"'data/processed' is not a directory"

def test_tests_directory_exists(project_root):
    """Verify T001d: tests/ directory exists."""
    tests_dir = project_root / "tests"
    assert tests_dir.exists(), f"Directory 'tests' missing at {tests_dir}"
    assert tests_dir.is_dir(), f"'tests' is not a directory"

def test_requirements_txt_exists(project_root):
    """Verify T002: requirements.txt exists at root."""
    req_file = project_root / "requirements.txt"
    assert req_file.exists(), f"File 'requirements.txt' missing at {req_file}"
    
    # Verify it contains expected dependencies
    content = req_file.read_text()
    required_pkgs = [
        "pandas", "numpy", "scikit-learn", "nibabel", 
        "requests", "pyyaml", "statsmodels", "scipy"
    ]
    for pkg in required_pkgs:
        assert pkg.lower() in content.lower(), f"Missing dependency '{pkg}' in requirements.txt"