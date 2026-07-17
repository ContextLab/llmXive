import os
from pathlib import Path
import pytest
import shutil
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_data_dirs import main

def test_data_directories_created(tmp_path):
    """
    Test that setup_data_dirs creates the required directory structure.
    We patch the working directory to use a temporary directory to avoid
    polluting the actual project tree during tests.
    """
    # Save original cwd
    original_cwd = os.getcwd()
    
    try:
        # Change to temp directory (simulating project root)
        os.chdir(tmp_path)
        
        # Create a dummy code directory so the script's logic finds the parent
        (tmp_path / "code").mkdir()
        
        # Run the main function
        main()
        
        # Verify directories exist
        data_raw = tmp_path / "data" / "raw"
        data_processed = tmp_path / "data" / "processed"
        data_consent = tmp_path / "data" / "consent"
        
        assert data_raw.exists(), "data/raw directory was not created"
        assert data_raw.is_dir(), "data/raw is not a directory"
        
        assert data_processed.exists(), "data/processed directory was not created"
        assert data_processed.is_dir(), "data/processed is not a directory"
        
        assert data_consent.exists(), "data/consent directory was not created"
        assert data_consent.is_dir(), "data/consent is not a directory"
        
    finally:
        # Restore original cwd
        os.chdir(original_cwd)
