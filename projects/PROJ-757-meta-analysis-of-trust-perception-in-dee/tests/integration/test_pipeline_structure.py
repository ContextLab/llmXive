"""
Integration tests to verify the pipeline directory structure and file existence.
"""
import os
import pytest
from pathlib import Path

def test_project_structure_exists():
    """Verify that the required project directories exist."""
    base = Path(__file__).parent.parent.parent
    
    required_dirs = [
        "code",
        "data",
        "data/search_results",
        "data/screening",
        "data/harmonized",
        "results",
        "results/analysis",
        "results/figures",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    for dir_name in required_dirs:
        dir_path = base / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_requirements_txt_exists():
    """Verify that requirements.txt exists at the root."""
    base = Path(__file__).parent.parent.parent
    req_file = base / "requirements.txt"
    assert req_file.exists(), "requirements.txt is missing"

def test_pytest_config_exists():
    """Verify that pytest configuration exists (conftest.py)."""
    base = Path(__file__).parent.parent.parent
    conftest = base / "tests" / "conftest.py"
    # Note: conftest.py is in tests/, not tests/unit/
    assert conftest.exists(), "tests/conftest.py is missing"
