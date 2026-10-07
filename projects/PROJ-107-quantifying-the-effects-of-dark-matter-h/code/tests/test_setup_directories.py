"""
Tests for the directory setup functionality.
Verifies that T001b and related setup tasks create the correct structure.
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Ensure code is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_directories import create_project_structure


class TestProjectStructure:
    """Test suite for project directory creation."""

    def test_creates_required_data_directories(self, tmp_path):
        """
        Verify T001b: Creates data/ and subdirectories (raw, processed, metadata).
        Specifically checks for tng100 and millennium raw folders.
        """
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup
            create_project_structure()

            # Verify required data paths exist
            assert (tmp_path / "data").exists(), "data/ directory missing"
            assert (tmp_path / "data/raw").exists(), "data/raw/ directory missing"
            assert (tmp_path / "data/raw/tng100").exists(), "data/raw/tng100/ missing"
            assert (tmp_path / "data/raw/millennium").exists(), "data/raw/millennium/ missing"
            assert (tmp_path / "data/processed").exists(), "data/processed/ missing"
            assert (tmp_path / "data/metadata").exists(), "data/metadata/ missing"
        
        finally:
            os.chdir(original_cwd)

    def test_creates_required_code_directories(self, tmp_path):
        """
        Verify T001a: Creates code/ and subdirectories.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            create_project_structure()

            assert (tmp_path / "code").exists()
            assert (tmp_path / "code/ingestion").exists()
            assert (tmp_path / "code/processing").exists()
            assert (tmp_path / "code/analysis").exists()
            assert (tmp_path / "code/utils").exists()
            assert (tmp_path / "code/tests").exists()
        finally:
            os.chdir(original_cwd)

    def test_creates_output_directories(self, tmp_path):
        """
        Verify T001c: Creates outputs/ and docs/ directories.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            create_project_structure()

            assert (tmp_path / "outputs").exists()
            assert (tmp_path / "outputs/figures").exists()
            assert (tmp_path / "outputs/reports").exists()
            assert (tmp_path / "docs").exists()
            assert (tmp_path / "state").exists()
        finally:
            os.chdir(original_cwd)

    def test_no_duplicates_on_rerun(self, tmp_path):
        """
        Verify that running the setup twice does not cause errors or duplicate creation logic.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # First run
            count1 = create_project_structure()
            
            # Second run (should not raise and should create 0 new dirs)
            count2 = create_project_structure()
            
            assert count2 == 0, "Second run should create 0 new directories"
        finally:
            os.chdir(original_cwd)