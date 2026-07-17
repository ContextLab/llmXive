"""
Unit tests for setup_project_root.py (T005).
Verifies that the project root directory is created correctly.
"""
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_project_root import setup_project_root


class TestSetupProjectRoot:
    """Tests for the setup_project_root function."""

    def test_creates_directory(self, tmp_path):
        """Test that the function creates the project root directory."""
        # Change to temporary directory to avoid polluting actual projects/
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            project_name = "PROJ-TEST-001"
            project_root = setup_project_root(project_name)

            # Verify directory exists
            assert project_root.exists(), "Project root directory should exist"
            assert project_root.is_dir(), "Project root should be a directory"
            assert project_root.name == project_name, "Directory name should match project name"
        finally:
            os.chdir(original_cwd)

    def test_creates_nested_structure(self, tmp_path):
        """Test that the function creates parent directories if needed."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            project_name = "PROJ-TEST-002"
            project_root = setup_project_root(project_name)

            # Verify parent 'projects' directory was created
            parent_dir = project_root.parent
            assert parent_dir.exists(), "Parent 'projects' directory should exist"
            assert parent_dir.is_dir(), "Parent should be a directory"
        finally:
            os.chdir(original_cwd)

    def test_idempotent_creation(self, tmp_path):
        """Test that calling the function twice doesn't cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            project_name = "PROJ-TEST-003"

            # First call
            project_root1 = setup_project_root(project_name)
            assert project_root1.exists()

            # Second call should not raise
            project_root2 = setup_project_root(project_name)
            assert project_root2.exists()
            assert project_root1 == project_root2
        finally:
            os.chdir(original_cwd)

    def test_creates_actual_project_name(self, tmp_path):
        """Test that the actual project name from T005 is created correctly."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            project_name = "PROJ-964-llmxive-follow-up-extending-wan-streamer"
            project_root = setup_project_root(project_name)

            assert project_root.exists()
            assert project_root.is_dir()
            assert project_root.name == project_name
            assert project_root.parent.name == "projects"
        finally:
            os.chdir(original_cwd)

    def test_path_structure(self, tmp_path):
        """Test the full path structure matches requirements."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            project_name = "PROJ-964-llmxive-follow-up-extending-wan-streamer"
            project_root = setup_project_root(project_name)

            expected_path = tmp_path / "projects" / project_name
            assert project_root == expected_path, f"Expected {expected_path}, got {project_root}"
        finally:
            os.chdir(original_cwd)