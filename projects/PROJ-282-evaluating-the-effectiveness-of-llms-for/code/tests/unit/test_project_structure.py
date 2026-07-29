"""
Unit tests to verify the project directory structure exists as required by T001.
"""
import os
import pytest
from pathlib import Path

# Determine the root directory relative to this test file
# Assuming tests are in code/tests/unit/
TEST_DIR = Path(__file__).resolve().parent
ROOT_DIR = TEST_DIR.parent.parent  # code/
REPO_ROOT = ROOT_DIR.parent         # repository root

REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "state",
    "state/projects"
]

class TestProjectStructure:
    def test_root_directories_exist(self):
        """Verify top-level directories exist."""
        for dir_name in ["src", "tests", "data", "state"]:
            path = REPO_ROOT / dir_name
            assert path.exists(), f"Directory missing: {path}"
            assert path.is_dir(), f"Not a directory: {path}"

    def test_data_subdirectories_exist(self):
        """Verify data subdirectories exist."""
        subdirs = ["raw", "processed", "results", "human_review"]
        for subdir in subdirs:
            path = REPO_ROOT / "data" / subdir
            assert path.exists(), f"Missing data subdirectory: {path}"
            assert path.is_dir(), f"Not a directory: {path}"

    def test_state_projects_exists(self):
        """Verify state/projects directory exists."""
        path = REPO_ROOT / "state" / "projects"
        assert path.exists(), f"Missing state/projects: {path}"
        assert path.is_dir(), f"Not a directory: {path}"

    def test_src_structure_exists(self):
        """Verify src subdirectories exist."""
        subdirs = ["utils", "models", "data", "services", "analysis"]
        for subdir in subdirs:
            path = REPO_ROOT / "src" / subdir
            assert path.exists(), f"Missing src subdirectory: {path}"
            assert path.is_dir(), f"Not a directory: {path}"
