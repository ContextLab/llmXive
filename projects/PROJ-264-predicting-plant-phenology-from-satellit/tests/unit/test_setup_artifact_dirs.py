import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_artifact_dirs import main

def test_create_directories():
    """
    Test that the script creates the artifacts and artifacts/models directories.
    We run this in a temporary directory to avoid polluting the actual project tree
    during testing, but we verify the logic holds.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to the temp directory to simulate running from project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run the main function
            exit_code = main()
            
            # Assert the function returned success
            assert exit_code == 0, "main() should return 0 on success"
            
            # Verify directories exist
            artifacts_dir = Path(tmpdir) / "artifacts"
            models_dir = Path(tmpdir) / "artifacts" / "models"
            
            assert artifacts_dir.exists(), "artifacts/ directory should exist"
            assert artifacts_dir.is_dir(), "artifacts/ should be a directory"
            
            assert models_dir.exists(), "artifacts/models/ directory should exist"
            assert models_dir.is_dir(), "artifacts/models/ should be a directory"
            
        finally:
            os.chdir(original_cwd)

def test_directories_already_exist():
    """
    Test that the script handles the case where directories already exist
    without raising an error.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Pre-create the directories
            artifacts_dir = Path(tmpdir) / "artifacts"
            models_dir = artifacts_dir / "models"
            artifacts_dir.mkdir(parents=True)
            models_dir.mkdir(parents=True)
            
            # Run the main function
            exit_code = main()
            
            # Should still succeed
            assert exit_code == 0
            
        finally:
            os.chdir(original_cwd)