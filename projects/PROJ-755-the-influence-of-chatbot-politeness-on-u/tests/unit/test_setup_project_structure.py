import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path so we can import the module
# This assumes the test is run from the project root or the code directory is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_structure_creates_all_directories(temp_project_root):
    """Test that create_structure creates all required directories."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "state",
    ]

    # Verify directories do not exist before running
    for dir_path in required_dirs:
        assert not (temp_project_root / dir_path).exists(), f"Directory {dir_path} should not exist before test"

    # Run the function
    create_structure()

    # Verify directories exist after running
    for dir_path in required_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} was not created"
        assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_create_structure_idempotent(temp_project_root):
    """Test that running create_structure multiple times does not cause errors."""
    create_structure()
    # Run again
    create_structure()
    # Should not raise an error
    assert True
