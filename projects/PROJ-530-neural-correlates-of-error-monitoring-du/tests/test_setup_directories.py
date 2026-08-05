import os
import pytest
from pathlib import Path
from code.setup_directories import create_project_directories

class TestSetupDirectories:
    def test_create_project_directories_creates_data_dirs(self, tmp_path, monkeypatch):
        """
        Test that the function creates the specific data directories required by T002.
        We patch the project root to use a temporary directory to avoid cluttering the real repo.
        """
        # Mock the project root to be inside the temp path
        mock_project_root = tmp_path / "projects" / "PROJ-530-neural-correlates-of-error-monitoring-du"
        
        # We need to patch the function to use our temp path instead of the hardcoded string
        # Since the function constructs the path internally, we will run it and check the result
        # relative to the current working directory, or we can refactor slightly to be injectable.
        # For this test, we will change the working directory to tmp_path and expect the function
        # to create the structure there.
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the function
            result = create_project_directories()
            
            assert result is True
            
            # Verify the specific paths from T002 exist
            data_raw = mock_project_root / "data" / "raw"
            data_processed = mock_project_root / "data" / "processed"
            
            assert data_raw.exists(), f"Directory {data_raw} was not created"
            assert data_raw.is_dir(), f"{data_raw} exists but is not a directory"
            
            assert data_processed.exists(), f"Directory {data_processed} was not created"
            assert data_processed.is_dir(), f"{data_processed} exists but is not a directory"
            
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path, monkeypatch):
        """
        Test that running the function twice does not raise errors.
        """
        mock_project_root = tmp_path / "projects" / "PROJ-530-neural-correlates-of-error-monitoring-du"
        original_cwd = os.getcwd()
        
        try:
            os.chdir(tmp_path)
            
            # Run twice
            create_project_directories()
            create_project_directories()
            
            # Verify existence
            assert (mock_project_root / "data" / "raw").exists()
            assert (mock_project_root / "data" / "processed").exists()
            
        finally:
            os.chdir(original_cwd)