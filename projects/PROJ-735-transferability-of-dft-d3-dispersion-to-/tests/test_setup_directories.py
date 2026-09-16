import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to import the function from the code module
# Since we are running tests, we adjust the path to include the code directory
import sys
from pathlib import Path

# Add parent of code to path if running from tests directory
code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_directories import main

def test_directories_created():
    """Test that setup_directories creates the required directories."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the project root by changing current working directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Run the setup
            main()
            
            # Verify directories exist
            data_raw = Path(tmpdir) / "data" / "raw"
            data_derived = Path(tmpdir) / "data" / "derived"
            
            assert data_raw.exists(), "data/raw directory was not created"
            assert data_raw.is_dir(), "data/raw is not a directory"
            
            assert data_derived.exists(), "data/derived directory was not created"
            assert data_derived.is_dir(), "data/derived is not a directory"
            
        finally:
            os.chdir(original_cwd)

def test_directories_already_exist():
    """Test that setup_directories handles existing directories gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Pre-create the directories
            data_raw = Path(tmpdir) / "data" / "raw"
            data_derived = Path(tmpdir) / "data" / "derived"
            data_raw.mkdir(parents=True)
            data_derived.mkdir(parents=True)
            
            # Run the setup - should not raise
            main()
            
            # Verify they still exist
            assert data_raw.exists()
            assert data_derived.exists()
            
        finally:
            os.chdir(original_cwd)