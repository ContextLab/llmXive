import os
import tempfile
import shutil
import pytest
import sys

# Ensure we can import from the code directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_directories import create_project_structure

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to simulate project root."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_creates_required_directories(temp_project_root):
    """Test that create_project_structure creates all required subdirectories."""
    required_dirs = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts",
    ]

    # Verify directories do not exist before
    for d in required_dirs:
        assert not os.path.exists(d), f"Directory {d} should not exist before creation"

    # Run the function
    create_project_structure()

    # Verify directories exist after
    for d in required_dirs:
        assert os.path.exists(d), f"Directory {d} was not created"
        assert os.path.isdir(d), f"{d} is not a directory"

def test_idempotent(temp_project_root):
    """Test that running the function twice does not raise errors."""
    create_project_structure()
    # Run again
    create_project_structure()
    # Should still exist
    assert os.path.exists("code")
    assert os.path.exists("data/raw")