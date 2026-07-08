"""
Tests for the project structure setup script.
Verifies that all required directories are created.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import the setup script
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_structure import main

def test_setup_creates_directories():
    """Test that the setup script creates all required directories."""
    # Create a temporary directory to simulate a project root
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run the setup script
            result = main()
            
            # Check return code
            assert result == 0, "Setup script should return 0 on success"
            
            # Verify required directories exist
            required_dirs = [
                "code", "data", "paper", "contracts", "tests",
                "data/raw", "data/processed", "data/results", "paper/figures"
            ]
            
            for d in required_dirs:
                full_path = Path(tmpdir) / d
                assert full_path.exists(), f"Required directory {d} was not created"
                assert full_path.is_dir(), f"{d} exists but is not a directory"
                
        finally:
            os.chdir(original_cwd)

def test_setup_idempotent():
    """Test that running setup twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run setup twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0, "First run should succeed"
            assert result2 == 0, "Second run should succeed"
            
        finally:
            os.chdir(original_cwd)