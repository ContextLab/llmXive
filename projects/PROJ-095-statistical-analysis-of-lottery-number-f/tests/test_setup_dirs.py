"""
Unit tests for setup_dirs.py (T001a).
Verifies that the directory structure is created correctly.
"""
import os
import shutil
import tempfile
import pytest
from code.setup_dirs import main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that main() creates the required directories."""
    # Directories that should be created
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "config"
    ]

    # Verify they do not exist before running
    for d in required_dirs:
        assert not os.path.exists(d), f"Directory {d} should not exist before setup"

    # Run the setup
    exit_code = main()

    # Verify exit code is 0 (success)
    assert exit_code == 0, "main() should return 0 on success"

    # Verify all directories now exist
    for d in required_dirs:
        assert os.path.exists(d), f"Directory {d} should exist after setup"
        assert os.path.isdir(d), f"{d} should be a directory"

def test_directories_persist_if_exist(temp_project_root):
    """Test that main() handles existing directories gracefully."""
    # Create one directory manually
    os.makedirs("data/raw", exist_ok=True)

    # Run setup
    exit_code = main()

    # Should still succeed
    assert exit_code == 0
    assert os.path.exists("data/raw")