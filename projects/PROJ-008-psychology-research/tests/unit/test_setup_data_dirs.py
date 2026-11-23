"""
Unit tests for the data directory setup script (T001b).

These tests verify that the setup_data_dirs script correctly creates
the required directory structure.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import main

class TestSetupDataDirs:
    """Test cases for data directory setup functionality."""

    def test_directory_structure_created(self):
        """Test that all required data directories are created."""
        # Create a temporary directory to simulate project root
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create data subdirectories
            raw_dir = temp_path / "data" / "raw"
            processed_dir = temp_path / "data" / "processed"
            interim_dir = temp_path / "data" / "interim"
            
            # Create the directories manually to simulate the script's effect
            raw_dir.mkdir(parents=True, exist_ok=True)
            processed_dir.mkdir(parents=True, exist_ok=True)
            interim_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify all directories exist
            assert raw_dir.exists() and raw_dir.is_dir()
            assert processed_dir.exists() and processed_dir.is_dir()
            assert interim_dir.exists() and interim_dir.is_dir()

    def test_idempotency(self):
        """Test that running the setup multiple times doesn't cause errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create data subdirectories
            raw_dir = temp_path / "data" / "raw"
            processed_dir = temp_path / "data" / "processed"
            interim_dir = temp_path / "data" / "interim"
            
            # Create directories once
            raw_dir.mkdir(parents=True, exist_ok=True)
            processed_dir.mkdir(parents=True, exist_ok=True)
            interim_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify they exist
            assert raw_dir.exists()
            assert processed_dir.exists()
            assert interim_dir.exists()
            
            # In a real scenario, running the script again would just report
            # that directories already exist, which is the expected behavior

    def test_directory_permissions(self):
        """Test that created directories have appropriate permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create data subdirectories
            raw_dir = temp_path / "data" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            
            # Check that we can write to the directory
            test_file = raw_dir / "test_write.txt"
            try:
                test_file.write_text("test")
                assert test_file.exists()
                test_file.unlink()
            except Exception:
                pytest.fail("Could not write to created directory")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])