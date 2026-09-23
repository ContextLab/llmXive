import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project import main

class TestSetupProject:
    """Test suite for project structure creation."""

    def test_directory_structure_created(self, tmp_path, monkeypatch):
        """Test that the script creates all required directories."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)
        
        # Run the setup
        result = main()
        
        # Verify return code
        assert result == 0, "main() should return 0 on success"
        
        # Verify all required directories exist
        required_dirs = [
            "code",
            "data",
            "tests",
            "state",
            "reports",
            "models",
            "data/raw",
            "data/processed"
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_nested_directories_created(self, tmp_path, monkeypatch):
        """Test that nested directories like data/raw and data/processed are created."""
        monkeypatch.chdir(tmp_path)
        main()
        
        # Check specific nested paths
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()

    def test_idempotent_creation(self, tmp_path, monkeypatch, capsys):
        """Test that running the script twice doesn't fail and reports existing dirs."""
        monkeypatch.chdir(tmp_path)
        
        # First run
        result1 = main()
        assert result1 == 0
        
        # Second run
        result2 = main()
        assert result2 == 0
        
        # Verify directories still exist
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data").exists()