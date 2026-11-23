"""
Tests for Data Directory Initialization (T001b).

Verifies that the setup_data_directories script correctly creates
the required directory structure: raw, processed, results, models.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the code directory to the path to import the setup module
# This assumes tests are run from the project root or via pytest with proper config
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from setup_data_directories import create_directories, verify_integrity, get_project_root


class TestDataDirectoryInitialization:
    """Test suite for data directory creation and verification."""

    def test_create_directories_structure(self, tmp_path):
        """
        Test that create_directories creates the correct subdirectories.
        """
        # Create a temporary project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Execute creation
        results = create_directories(project_root)

        # Verify keys in results
        expected_keys = [
            "data/raw",
            "data/processed",
            "data/results",
            "data/models"
        ]

        assert len(results) == 4, "Expected exactly 4 directory creation results"

        for key in expected_keys:
            assert key in results, f"Missing expected directory key: {key}"
            assert results[key] is True, f"Directory creation failed for: {key}"

        # Verify actual filesystem existence
        for key in expected_keys:
            dir_path = project_root / key
            assert dir_path.exists(), f"Directory {dir_path} does not exist on disk"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_verify_integrity_success(self, tmp_path):
        """
        Test verify_integrity returns True when all directories exist.
        """
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Create the structure manually first
        create_directories(project_root)

        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/results",
            "data/models"
        ]

        assert verify_integrity(project_root, expected_dirs) is True

    def test_verify_integrity_failure(self, tmp_path):
        """
        Test verify_integrity returns False when a directory is missing.
        """
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Create partial structure
        (project_root / "data").mkdir()
        (project_root / "data" / "raw").mkdir()
        # Intentionally missing 'processed', 'results', 'models'

        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/results",
            "data/models"
        ]

        assert verify_integrity(project_root, expected_dirs) is False

    def test_idempotency(self, tmp_path):
        """
        Test that running create_directories multiple times does not fail.
        """
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # First run
        results1 = create_directories(project_root)
        assert all(results1.values())

        # Second run (should succeed without error)
        results2 = create_directories(project_root)
        assert all(results2.values())

        # Verify counts remain consistent
        assert len(list((project_root / "data").iterdir())) == 4
