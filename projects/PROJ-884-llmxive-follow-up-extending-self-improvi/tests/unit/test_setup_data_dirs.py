"""
Unit tests for setup_data_dirs.py
"""
import os
import tempfile
import pytest
from pathlib import Path
from code.setup_data_dirs import setup_data_directories

def test_setup_data_directories_creates_structure():
    """Test that setup_data_directories creates the required structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        result = setup_data_directories(base_path)
        
        # Check that all directories were created
        assert len(result) == 3
        assert (base_path / "data").exists()
        assert (base_path / "data" / "raw").exists()
        assert (base_path / "data" / "processed").exists()

def test_setup_data_directories_verifies_writability():
    """Test that setup_data_directories verifies directories are writable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        result = setup_data_directories(base_path)
        
        # Try to write a file to each directory
        for directory in result:
            test_file = directory / "writability_test.txt"
            try:
                with open(test_file, 'w') as f:
                    f.write("test content")
                with open(test_file, 'r') as f:
                    content = f.read()
                assert content == "test content"
                test_file.unlink()
            except OSError:
                pytest.fail(f"Directory {directory} is not writable")

def test_setup_data_directories_idempotent():
    """Test that running setup_data_directories twice doesn't fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # First run
        result1 = setup_data_directories(base_path)
        assert len(result1) == 3
        
        # Second run
        result2 = setup_data_directories(base_path)
        assert len(result2) == 3

def test_setup_data_directories_handles_existing_dirs():
    """Test that setup_data_directories handles existing directories gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Manually create the structure
        (base_path / "data").mkdir()
        (base_path / "data" / "raw").mkdir()
        (base_path / "data" / "processed").mkdir()
        
        # Run setup - should not fail
        result = setup_data_directories(base_path)
        assert len(result) == 3
        
        # Verify they are the same directories
        assert result[0] == base_path / "data"
        assert result[1] == base_path / "data" / "raw"
        assert result[2] == base_path / "data" / "processed"