"""
Unit tests for Task T005: Project Structure Creation.

This test suite verifies that the directory structure for 
PROJ-964-llmxive-follow-up-extending-wan-streamer is correctly created 
and persists on disk.
"""
import os
import sys
import pytest
from pathlib import Path
import shutil
import tempfile

# Add the project root to the path if running from tests/
# Assuming this file is at tests/unit/test_t005_project_structure.py
# and the script is at code/tasks/setup_project_structure.py
# We need to import the logic or run the script.
# Since T005 is a setup script, we will test the existence of the directories
# that the script is supposed to create.

PROJECT_ID = "PROJ-964-llmxive-follow-up-extending-wan-streamer"
PROJECT_ROOT_PATH = Path("projects") / PROJECT_ID

REQUIRED_SUBDIRS = [
    "src",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/models",
    "data/metrics",
    "docs",
    "state",
    "contracts",
]

class TestT005ProjectStructure:
    """Tests for T005 directory creation."""

    def test_project_root_exists(self):
        """Verify the main project directory exists."""
        assert PROJECT_ROOT_PATH.exists(), f"Project root {PROJECT_ROOT_PATH} does not exist."
        assert PROJECT_ROOT_PATH.is_dir(), f"{PROJECT_ROOT_PATH} is not a directory."

    @pytest.mark.parametrize("subdir", REQUIRED_SUBDIRS)
    def test_required_subdirectory_exists(self, subdir):
        """Verify each required subdirectory exists."""
        full_path = PROJECT_ROOT_PATH / subdir
        assert full_path.exists(), f"Subdirectory {full_path} does not exist."
        assert full_path.is_dir(), f"{full_path} is not a directory."

    def test_all_directories_are_writable(self):
        """Verify we can write a temporary file to each directory (sanity check)."""
        # This ensures permissions are correct
        for subdir in REQUIRED_SUBDIRS:
            full_path = PROJECT_ROOT_PATH / subdir
            test_file = full_path / ".write_test_temp"
            try:
                test_file.touch()
                test_file.unlink()
            except OSError as e:
                pytest.fail(f"Cannot write to {full_path}: {e}")

    def test_structure_matches_spec(self):
        """
        Comprehensive check that the structure matches the T005 spec.
        This aggregates the checks above into a single logical assertion.
        """
        errors = []
        
        if not PROJECT_ROOT_PATH.exists():
            errors.append(f"Root missing: {PROJECT_ROOT_PATH}")
        
        for subdir in REQUIRED_SUBDIRS:
            full_path = PROJECT_ROOT_PATH / subdir
            if not full_path.exists():
                errors.append(f"Missing: {full_path}")
            elif not full_path.is_dir():
                errors.append(f"Not a dir: {full_path}")
        
        if errors:
            pytest.fail(f"Structure verification failed:\n" + "\n".join(errors))