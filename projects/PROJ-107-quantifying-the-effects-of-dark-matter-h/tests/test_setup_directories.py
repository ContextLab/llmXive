import pytest
import os
import sys
from pathlib import Path
from code.setup_directories import create_project_structure

class TestProjectStructure:
    """
    Tests to verify that the project structure is correctly created by T001.
    """

    def test_create_project_structure_creates_dirs(self, tmp_path):
        """
        Verify that create_project_structure creates the required directories.
        We run it in a temporary directory to avoid polluting the real project
        during testing, but the logic remains the same.
        """
        # Change to temp directory to simulate running the script there
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            
            # Run the function
            result = create_project_structure()
            
            assert result is True
            
            # Verify specific directories exist
            assert (tmp_path / "code").is_dir()
            assert (tmp_path / "code/utils").is_dir()
            assert (tmp_path / "code/ingestion").is_dir()
            assert (tmp_path / "code/processing").is_dir()
            assert (tmp_path / "code/analysis").is_dir()
            assert (tmp_path / "code/tests").is_dir()
            
            assert (tmp_path / "data").is_dir()
            assert (tmp_path / "data/raw").is_dir()
            assert (tmp_path / "data/processed").is_dir()
            
            assert (tmp_path / "outputs").is_dir()
            assert (tmp_path / "outputs/figures").is_dir()
            assert (tmp_path / "outputs/reports").is_dir()
            
            assert (tmp_path / "docs").is_dir()
            assert (tmp_path / "state").is_dir()
            
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """
        Verify that running the function twice does not raise errors
        (directories should already exist).
        """
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            
            # Run once
            create_project_structure()
            
            # Run again
            result = create_project_structure()
            
            assert result is True
            
        finally:
            os.chdir(original_cwd)