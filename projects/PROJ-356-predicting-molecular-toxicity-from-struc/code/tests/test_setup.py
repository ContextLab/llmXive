import os
import sys
from pathlib import Path
import pytest
from setup_directories import main

def test_data_directory_exists():
    """Verify that the results directory exists after setup."""
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    assert results_dir.exists(), f"Results directory {results_dir} does not exist"
    assert results_dir.is_dir(), f"{results_dir} is not a directory"

def test_setup_script_creates_results_dir():
    """Verify that running the setup script creates the results directory."""
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    
    # Remove if exists for clean test
    if results_dir.exists():
        import shutil
        shutil.rmtree(results_dir)
        
    # Run setup
    main()
    
    # Verify creation
    assert results_dir.exists(), "Setup script failed to create results directory"
    assert results_dir.is_dir(), "Results path is not a directory"
