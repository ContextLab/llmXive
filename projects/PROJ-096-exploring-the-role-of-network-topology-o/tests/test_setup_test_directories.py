"""
Tests for the setup_test_directories module.
Verifies that the correct directory structure is created.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys
import pytest

# Add the code directory to the path for imports
# Assuming tests are run from the project root or the test runner handles path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_test_directories import create_test_directories


def test_create_test_directories():
    """Test that create_test_directories creates the expected folders."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)

        # Call the function
        create_test_directories(base_path)

        # Verify directories exist
        assert (base_path / "tests").exists(), "tests directory not created"
        assert (base_path / "state").exists(), "state directory not created"
        assert (base_path / "state" / "projects").exists(), "state/projects directory not created"

        # Verify they are directories
        assert (base_path / "tests").is_dir(), "tests is not a directory"
        assert (base_path / "state").is_dir(), "state is not a directory"
        assert (base_path / "state" / "projects").is_dir(), "state/projects is not a directory"


def test_create_test_directories_idempotent():
    """Test that running the function multiple times does not cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)

        # Run twice
        create_test_directories(base_path)
        create_test_directories(base_path)

        # Verify directories still exist
        assert (base_path / "tests").exists()
        assert (base_path / "state" / "projects").exists()


def test_create_test_directories_partial_existing():
    """Test behavior when some directories already exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)

        # Manually create 'tests' but not 'state'
        (base_path / "tests").mkdir()

        # Run the function
        create_test_directories(base_path)

        # Verify both exist now
        assert (base_path / "tests").exists()
        assert (base_path / "state").exists()
        assert (base_path / "state" / "projects").exists()
