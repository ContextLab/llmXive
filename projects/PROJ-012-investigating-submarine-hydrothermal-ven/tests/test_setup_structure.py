"""
Tests for the project structure setup script.

Verifies that the required directories are created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the parent directory to the path to allow importing code.setup_structure
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_setup_creates_required_directories():
    """Test that the setup script creates all required directories."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Import and run the setup logic directly (avoiding subprocess for cleaner testing)
            from code.setup_structure import main
            
            # We need to capture the output or just run it. 
            # Since main() prints, we'll just run it and then check the filesystem.
            main()
            
            # Define the expected directories relative to temp_dir
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "state",
                "results/figures"
            ]
            
            # Verify each directory exists
            for dir_path in required_dirs:
                full_path = Path(temp_dir) / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created."
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory."
                
                # Verify .gitkeep exists
                gitkeep_path = full_path / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep not found in {dir_path}."
                
        finally:
            os.chdir(original_cwd)

def test_setup_idempotent():
    """Test that running the setup script twice does not cause errors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            from code.setup_structure import main
            
            # Run twice
            main()
            main()
            
            # Should still exist and be valid
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "state",
                "results/figures"
            ]
            
            for dir_path in required_dirs:
                full_path = Path(temp_dir) / dir_path
                assert full_path.exists()
                
        finally:
            os.chdir(original_cwd)