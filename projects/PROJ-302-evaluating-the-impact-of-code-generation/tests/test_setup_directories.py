"""
Unit tests for the directory setup functionality.
"""
import os
import pytest
from pathlib import Path
from code.setup_directories import create_directories

def test_create_directories_creates_core_structure():
    """Test that create_directories creates all required core directories."""
    # Ensure directories don't exist before test (clean state)
    # Note: In a real CI environment, we might want to clean up after ourselves
    
    result = create_directories()
    assert result is True
    
    # Verify core directories exist
    base_path = Path(".")
    assert (base_path / "code").exists()
    assert (base_path / "data").exists()
    assert (base_path / "tests").exists()
    assert (base_path / "docs").exists()
    
    # Verify data subdirectories
    assert (base_path / "data" / "raw").exists()
    assert (base_path / "data" / "processed").exists()
    
    # Verify code subdirectories
    assert (base_path / "code" / "data_acquisition").exists()
    assert (base_path / "code" / "feature_extraction").exists()
    assert (base_path / "code" / "analysis").exists()
    assert (base_path / "code" / "utils").exists()
    
    # Verify empty checksums.yaml file
    checksums_file = base_path / "data" / "checksums.yaml"
    assert checksums_file.exists()
    assert checksums_file.stat().st_size == 0

def test_create_directories_idempotent():
    """Test that running create_directories multiple times doesn't cause errors."""
    # Run twice
    result1 = create_directories()
    result2 = create_directories()
    
    assert result1 is True
    assert result2 is True
    
    # Verify structure still intact
    base_path = Path(".")
    assert (base_path / "code").exists()
    assert (base_path / "data").exists()
    assert (base_path / "tests").exists()
    assert (base_path / "docs").exists()