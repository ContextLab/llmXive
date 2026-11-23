import os
from pathlib import Path
import pytest
from setup_data_dirs import main

def test_setup_data_dirs_creates_directories():
    """
    Test that setup_data_dirs creates the required directories and .gitkeep files.
    """
    # Ensure directories don't exist before test (optional cleanup)
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    # Run the setup
    main()
    
    # Verify directories exist
    assert raw_dir.exists(), "data/raw directory should exist"
    assert processed_dir.exists(), "data/processed directory should exist"
    
    # Verify .gitkeep files exist
    assert (raw_dir / ".gitkeep").exists(), "data/raw/.gitkeep should exist"
    assert (processed_dir / ".gitkeep").exists(), "data/processed/.gitkeep should exist"
    
    # Verify .gitkeep files are not empty (they should have content)
    assert (raw_dir / ".gitkeep").stat().st_size > 0, "data/raw/.gitkeep should not be empty"
    assert (processed_dir / ".gitkeep").stat().st_size > 0, "data/processed/.gitkeep should not be empty"