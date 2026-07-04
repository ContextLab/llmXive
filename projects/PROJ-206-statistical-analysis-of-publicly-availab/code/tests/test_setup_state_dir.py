import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path so we can import setup_state_dir
code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from setup_state_dir import main

def test_state_directory_creation(tmp_path):
    """Test that the state directory is created correctly."""
    # Change to the temporary directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run the main function
        result = main()
        
        # Check return code
        assert result == 0, "main() should return 0 on success"
        
        # Check that state directory exists
        state_dir = tmp_path / "state"
        assert state_dir.exists(), "state directory should be created"
        assert state_dir.is_dir(), "state should be a directory"
        
        # Check that projects subdirectory exists
        projects_dir = state_dir / "projects"
        assert projects_dir.exists(), "state/projects subdirectory should be created"
        assert projects_dir.is_dir(), "state/projects should be a directory"
        
    finally:
        os.chdir(original_cwd)

def test_state_directory_already_exists(tmp_path):
    """Test that the function handles existing state directory gracefully."""
    # Create the state directory manually first
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run the main function
        result = main()
        
        # Should still return 0
        assert result == 0, "main() should return 0 even if directory exists"
        
    finally:
        os.chdir(original_cwd)

def test_state_directory_permissions(tmp_path):
    """Test that the created directory has correct permissions."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        main()
        
        state_dir = tmp_path / "state"
        assert os.access(state_dir, os.R_OK), "state directory should be readable"
        assert os.access(state_dir, os.W_OK), "state directory should be writable"
        assert os.access(state_dir, os.X_OK), "state directory should be executable (traversable)"
        
    finally:
        os.chdir(original_cwd)