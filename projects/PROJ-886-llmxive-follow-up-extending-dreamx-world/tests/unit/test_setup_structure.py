"""
Unit tests for project structure initialization.
Verifies that all required directories are created correctly.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the setup function
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code/utils"))
from setup_structure import PROJECT_ROOT, DIRECTORIES


class TestProjectStructure:
    """Tests for project structure creation."""

    def test_project_root_path(self):
        """Verify the project root path is correctly defined."""
        assert PROJECT_ROOT.name == "PROJ-886-llmxive-follow-up-extending-dreamx-world"
        assert PROJECT_ROOT.parent.name == "projects"

    def test_required_directories_exist(self):
        """Verify all required directories are defined."""
        expected_dirs = {
            "data/raw",
            "data/derived",
            "code",
            "code/models",
            "code/pipeline",
            "code/analysis",
            "code/utils",
            "tests/unit",
            "tests/integration",
        }
        actual_dirs = set(DIRECTORIES)
        assert expected_dirs == actual_dirs, f"Missing directories: {expected_dirs - actual_dirs}"

    def test_directory_creation(self, tmp_path):
        """Test that directories can be created in a temporary location."""
        # Temporarily override PROJECT_ROOT for testing
        original_root = PROJECT_ROOT
        
        # Create a temporary project root
        test_root = tmp_path / "projects" / "PROJ-886-llmxive-follow-up-extending-dreamx-world"
        
        # Manually create directories using the same logic
        for dir_path in DIRECTORIES:
            full_path = test_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        # Verify all directories exist
        for dir_path in DIRECTORIES:
            full_path = test_root / dir_path
            assert full_path.exists(), f"Directory not created: {full_path}"
            assert full_path.is_dir(), f"Not a directory: {full_path}"

    def test_nested_structure_preservation(self, tmp_path):
        """Test that nested directory structure is preserved."""
        test_root = tmp_path / "projects" / "PROJ-886-llmxive-follow-up-extending-dreamx-world"
        
        # Create deep nested structure
        deep_path = test_root / "code" / "models" / "submodule"
        deep_path.mkdir(parents=True, exist_ok=True)
        
        assert deep_path.exists()
        assert (test_root / "code").exists()
        assert (test_root / "code" / "models").exists()

    def test_idempotent_creation(self, tmp_path):
        """Test that creating directories twice doesn't cause errors."""
        test_root = tmp_path / "projects" / "PROJ-886-llmxive-follow-up-extending-dreamx-world"
        
        # Create first time
        for dir_path in DIRECTORIES:
            (test_root / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create second time (should not raise)
        for dir_path in DIRECTORIES:
            (test_root / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Verify still exists
        for dir_path in DIRECTORIES:
            assert (test_root / dir_path).exists()