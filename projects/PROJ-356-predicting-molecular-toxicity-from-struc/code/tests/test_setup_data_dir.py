"""
Test for the create_data_dir script.
"""
import os
import sys
from pathlib import Path
import pytest
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.create_data_dir import main

def test_create_data_dir_creates_directory(tmp_path):
    """Test that the script creates the data directory."""
    # Create a temporary directory structure to simulate the project
    temp_code_dir = tmp_path / "code"
    temp_code_dir.mkdir()
    
    # Change to the temporary directory to run the script
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_code_dir)
        
        # Run the script
        result = main()
        
        # Check that the data directory was created
        data_dir = temp_code_dir / "data"
        assert data_dir.exists(), "Data directory was not created"
        assert data_dir.is_dir(), "Data path is not a directory"
        
        # Check for .gitkeep file
        gitkeep = data_dir / ".gitkeep"
        assert gitkeep.exists(), ".gitkeep file was not created"
        
        assert result == 0, "Script did not return 0"
    finally:
        os.chdir(original_cwd)