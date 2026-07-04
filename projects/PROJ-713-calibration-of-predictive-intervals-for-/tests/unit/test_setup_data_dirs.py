import os
import pytest
from pathlib import Path
import sys

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PROJECT_ROOT
from setup_data_dirs import ensure_dir, main

def test_ensure_dir_creates_directory():
    """Test that ensure_dir creates a directory if it doesn't exist."""
    test_dir = PROJECT_ROOT / "data" / "test_tmp_dir"
    
    # Ensure it doesn't exist initially
    if test_dir.exists():
        os.rmdir(test_dir)
        
    # Create it
    ensure_dir(test_dir)
    
    # Verify it exists
    assert test_dir.exists()
    assert test_dir.is_dir()
    
    # Cleanup
    os.rmdir(test_dir)

def test_ensure_dir_exists_no_error():
    """Test that ensure_dir doesn't raise if directory already exists."""
    test_dir = PROJECT_ROOT / "data" / "test_tmp_dir_2"
    ensure_dir(test_dir)
    
    # Call again - should not raise
    ensure_dir(test_dir)
    
    assert test_dir.exists()
    
    # Cleanup
    os.rmdir(test_dir)

def test_main_creates_data_dirs():
    """Test that main() creates the required data directories."""
    # Ensure they don't exist initially (for clean test)
    data_raw = PROJECT_ROOT / "data" / "raw"
    data_processed = PROJECT_ROOT / "data" / "processed"
    
    # Remove if they exist (rare but possible in test env)
    if data_raw.exists():
        os.rmdir(data_raw)
    if data_processed.exists():
        os.rmdir(data_processed)
    
    # Run main
    main()
    
    # Verify both exist
    assert data_raw.exists()
    assert data_raw.is_dir()
    assert data_processed.exists()
    assert data_processed.is_dir()