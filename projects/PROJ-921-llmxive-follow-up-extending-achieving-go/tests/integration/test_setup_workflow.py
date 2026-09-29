"""
Integration tests to verify the directory setup workflow.
"""
import os
import shutil
from pathlib import Path
import pytest

# Import the setup function
from code.setup_directories import setup_data_directories

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@pytest.fixture(autouse=True)
def ensure_clean_state():
    """Ensure directories exist before running tests."""
    setup_data_directories()
    yield

def test_setup_creates_all_directories():
    """Verify that running the setup function creates all required directories."""
    required_paths = [
        "code/data", "code/inference", "code/scoring", "code/analysis", "code/utils",
        "data/raw", "data/processed", "data/gold",
        "tests/unit", "tests/integration"
    ]
    
    for rel_path in required_paths:
        full_path = PROJECT_ROOT / rel_path
        assert full_path.exists(), f"Expected directory {full_path} to exist after setup"
        assert full_path.is_dir(), f"Expected {full_path} to be a directory"

def test_directory_structure_persistence():
    """Verify that directories persist after the setup function returns."""
    # Run setup
    created = setup_data_directories()
    
    # Verify specific test directories exist
    assert (PROJECT_ROOT / "tests" / "unit").exists()
    assert (PROJECT_ROOT / "tests" / "integration").exists()
    assert (PROJECT_ROOT / "code" / "data").exists()
    assert (PROJECT_ROOT / "data" / "processed").exists()