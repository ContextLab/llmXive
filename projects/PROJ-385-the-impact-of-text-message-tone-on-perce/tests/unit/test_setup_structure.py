"""
Unit tests for the project setup structure logic.
Verifies that the directory creation logic works as expected.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the function to test
# We mock the config to use a temporary directory for testing
from setup_project_structure import create_directories


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_create_directories_creates_all_required(temp_project_root):
    """Test that create_directories creates all required subdirectories."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/consent",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-text-tone-emotional-support",
        "specs/001-text-tone-emotional-support/contracts",
        "figures",
    ]

    with patch("setup_project_structure.get_project_root", return_value=temp_project_root):
        create_directories()

    for dir_name in required_dirs:
        full_path = temp_project_root / dir_name
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} is not a directory"


def test_create_directories_skips_existing(temp_project_root):
    """Test that create_directories does not fail if directories already exist."""
    # Pre-create some directories
    (temp_project_root / "code").mkdir()
    (temp_project_root / "data").mkdir()
    (temp_project_root / "data" / "raw").mkdir()

    with patch("setup_project_structure.get_project_root", return_value=temp_project_root):
        # Should run without error even if some dirs exist
        create_directories()

    # Verify they still exist
    assert (temp_project_root / "code").exists()
    assert (temp_project_root / "data" / "raw").exists()
