import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.setup_directories import setup_directories

class TestSetupDirectories:
    def test_directories_created(self, tmp_path, monkeypatch):
        """
        Test that setup_directories creates the required subdirectories.
        We use tmp_path to simulate a project root to avoid cluttering the real repo.
        """
        # Mock the project_root detection in setup_directories
        # We need to patch the variable inside the module or pass a custom root
        # Since the function uses a global `project_root` derived from __file__,
        # we will test the logic by creating a temporary structure that mimics the project.
        
        # Create a temp "project" structure
        temp_project = tmp_path / "project"
        temp_code = temp_project / "code"
        temp_code.mkdir(parents=True)
        
        # Create a dummy setup_directories.py in temp_code to control the path logic
        # Actually, easier: just run the function and check if it creates dirs relative to where it expects to be.
        # However, the function calculates `project_root` based on `__file__`.
        # To test this cleanly without moving files, we can patch the `project_root` variable in the module.
        
        import code.setup_directories as sd_module
        
        original_root = sd_module.project_root
        sd_module.project_root = temp_project
        
        try:
            result = sd_module.setup_directories()
            
            # Verify the expected directories exist
            assert result is not None
            assert "raw" in result
            assert "processed" in result
            assert "artifacts" in result
            
            # Check actual filesystem existence
            assert (temp_project / "data" / "raw").exists()
            assert (temp_project / "data" / "processed").exists()
            assert (temp_project / "data" / "artifacts").exists()
            assert (temp_project / "data" / "reports").exists()
            assert (temp_project / "data" / "results").exists()
            assert (temp_project / "data" / "models").exists()
            assert (temp_project / "data" / "figures").exists()
            
        finally:
            # Restore original
            sd_module.project_root = original_root

    def test_idempotent(self, tmp_path, monkeypatch):
        """
        Test that running setup_directories twice does not raise errors.
        """
        import code.setup_directories as sd_module
        temp_project = tmp_path / "project"
        temp_project.mkdir()
        
        original_root = sd_module.project_root
        sd_module.project_root = temp_project
        
        try:
            # Run twice
            sd_module.setup_directories()
            result2 = sd_module.setup_directories()
            
            assert result2 is not None
            assert (temp_project / "data" / "raw").exists()
        finally:
            sd_module.project_root = original_root
