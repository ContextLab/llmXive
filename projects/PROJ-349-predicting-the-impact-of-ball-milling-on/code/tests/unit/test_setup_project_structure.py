import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from setup_project_structure import setup_directories

class TestSetupProjectStructure:
    def test_setup_directories_creates_all_required_dirs(self, tmp_path):
        """
        Verify that setup_directories creates all required directories
        and places .gitkeep files in empty ones.
        """
        # Change to the temporary directory to simulate the project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Mock the parent path to point to tmp_path
            # Since the script uses Path(__file__).parent.parent, we need to
            # ensure the script thinks tmp_path is the correct base.
            # We will patch the base_path calculation inside the function
            # or simply run the function and check tmp_path contents.
            
            # A simpler approach: Patch the base_path variable in the module
            # or just verify the function creates dirs relative to where it's run.
            # Let's patch the module's base_path logic by mocking Path.
            
            # Actually, let's just run the function and verify the result.
            # The function determines base_path based on its location.
            # To test effectively, we should patch the base_path logic.
            
            with patch('setup_project_structure.Path') as mock_path:
                # Setup mock to return tmp_path for parent.parent
                mock_instance = MagicMock()
                mock_instance.parent.name = 'code' # Simulate being in code/
                mock_instance.parent.parent = tmp_path
                mock_path.return_value = mock_instance
                
                result = setup_directories()
                
                assert result is True
                
                # Verify directories exist
                required_dirs = [
                    "src",
                    "tests",
                    "data/raw",
                    "data/processed",
                    "data/splits",
                    "results",
                    "contracts",
                    ".github/workflows"
                ]
                
                for dir_name in required_dirs:
                    dir_path = tmp_path / dir_name
                    assert dir_path.exists(), f"Directory {dir_name} was not created"
                    assert dir_path.is_dir(), f"{dir_name} is not a directory"
                    
                    # Check for .gitkeep in empty directories
                    # Since we just created them, they should be empty or have .gitkeep
                    if not any(dir_path.iterdir()):
                        assert (dir_path / ".gitkeep").exists(), f".gitkeep missing in {dir_name}"
                        
        finally:
            os.chdir(original_cwd)

    def test_setup_directories_handles_existing_dirs(self, tmp_path):
        """
        Verify that setup_directories does not fail if directories already exist.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Pre-create one directory
            (tmp_path / "src").mkdir()
            
            with patch('setup_project_structure.Path') as mock_path:
                mock_instance = MagicMock()
                mock_instance.parent.name = 'code'
                mock_instance.parent.parent = tmp_path
                mock_path.return_value = mock_instance
                
                result = setup_directories()
                
                assert result is True
                assert (tmp_path / "src").exists()
                
        finally:
            os.chdir(original_cwd)