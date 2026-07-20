import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from code.setup_data_dirs import setup_directories


class TestSetupDataDirs:
    """Unit tests for data directory setup functionality."""

    def test_setup_directories_creates_data_structure(self):
        """Test that data directory structure is created correctly."""
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            
            # Call the function
            setup_directories(root)
            
            # Define expected data directories
            expected_dirs = [
                "data/raw",
                "data/processed",
                "data/splits",
                "results"
            ]
            
            # Verify each directory exists
            for dir_path in expected_dirs:
                full_path = root / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_setup_directories_creates_gitkeep_in_data_dirs(self):
        """Test that .gitkeep files are created in data directories."""
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            
            # Call the function
            setup_directories(root)
            
            # Check that .gitkeep files exist
            data_dirs = [
                "data/raw",
                "data/processed",
                "data/splits",
                "results"
            ]
            
            for dir_path in data_dirs:
                full_path = root / dir_path
                gitkeep = full_path / ".gitkeep"
                assert gitkeep.exists(), f".gitkeep not found in {dir_path}"

    def test_setup_directories_idempotent(self):
        """Test that running setup_directories twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            
            # Run twice
            setup_directories(root)
            setup_directories(root)  # Should not raise
            
            # Verify directories still exist
            assert (root / "data/raw").exists()
            assert (root / "results").exists()

    def test_setup_directories_creates_nested_structure(self):
        """Test that nested directory structures are created correctly."""
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            
            setup_directories(root)
            
            # Verify nested structure
            assert (root / "data" / "raw").exists()
            assert (root / "data" / "processed").exists()
            assert (root / "data" / "splits").exists()
            assert (root / "results").exists()