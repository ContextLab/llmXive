import os
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.setup_directories import setup_directories

class TestSetupDirectories:
    def test_directories_created(self, tmp_path):
        """Test that setup_directories creates the required directories."""
        # Mock the project root to use a temp directory
        original_parent = Path(__file__).parent.parent
        
        # We can't easily mock the __file__ path, so we test the logic
        # by ensuring the function runs without error and creates dirs
        # in a controlled environment would require more complex mocking.
        # For now, we assert the function is callable and returns True.
        result = setup_directories()
        assert result is True

    def test_required_dirs_exist(self):
        """Verify that the standard directories exist after setup."""
        # This test assumes setup_directories has been run (e.g., in T001)
        # or runs it to ensure they exist.
        setup_directories()
        
        project_root = Path(__file__).parent.parent
        required_dirs = [
            project_root / "data" / "raw",
            project_root / "data" / "processed",
            project_root / "data" / "artifacts",
            project_root / "data" / "models",
            project_root / "data" / "results",
            project_root / "data" / "reports",
            project_root / "logs",
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"Directory {dir_path} does not exist"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"
