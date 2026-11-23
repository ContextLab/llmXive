"""
Unit tests for create_artifact_dirs.py
"""
import os
import pytest
from pathlib import Path
import shutil

from create_artifact_dirs import main


@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure."""
    # Create the expected project root structure
    artifacts_root = tmp_path / "artifacts"
    artifacts_root.mkdir()
    return tmp_path


def test_artifact_directories_created(temp_project_root):
    """Test that the artifact directories are created."""
    # Change to the temp project root to simulate the script execution
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Create the code directory to match the script's location
        code_dir = temp_project_root / "code"
        code_dir.mkdir()
        
        # Create a dummy __init__.py so the import works if needed
        (code_dir / "__init__.py").touch()
        
        # Run the main function
        main()
        
        # Verify directories exist
        assert (temp_project_root / "artifacts" / "models").exists()
        assert (temp_project_root / "artifacts" / "reports").exists()
        assert (temp_project_root / "artifacts" / "figures").exists()
        
    finally:
        os.chdir(original_cwd)