import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the function to test
from code.setup_directories import create_directories


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        yield Path(temp_dir)
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


def test_create_directories_creates_all_required(temp_project_root):
    """
    Test that create_directories() creates all required directories:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - data/results/
    - data/logs/
    - contracts/
    """
    # Execute the function
    create_directories()
    
    # Define expected directories
    expected_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "contracts",
    ]
    
    # Verify each directory exists
    for dir_name in expected_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"


def test_create_directories_handles_existing(temp_project_root):
    """
    Test that create_directories() does not fail if directories already exist.
    """
    # Pre-create some directories
    (temp_project_root / "code").mkdir()
    (temp_project_root / "data").mkdir()
    (temp_project_root / "data/raw").mkdir()
    
    # Execute the function - should not raise an exception
    create_directories()
    
    # Verify they still exist
    assert (temp_project_root / "code").exists()
    assert (temp_project_root / "data/raw").exists()


def test_create_directories_creates_nested(temp_project_root):
    """
    Test that create_directories() creates nested directories (e.g., data/raw).
    """
    create_directories()
    
    # Verify nested structure
    assert (temp_project_root / "data").exists()
    assert (temp_project_root / "data/raw").exists()
    assert (temp_project_root / "data/processed").exists()
    assert (temp_project_root / "data/results").exists()
    assert (temp_project_root / "data/logs").exists()
    assert (temp_project_root / "contracts").exists()
