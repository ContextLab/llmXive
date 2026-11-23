"""
Unit tests for the source directory setup script.

Tests that the required directories are created and that they are valid Python packages.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to import the function from the script. 
# Since the script is in code/, we need to adjust sys.path or import it directly.
# For simplicity in this test, we will import the function logic directly.

def test_source_directories_created(tmp_path):
    """Test that the source directories are created correctly."""
    # Change to the temporary directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Import the main function from the script
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
        from setup_source_dirs import main
        
        # Run the setup
        main()
        
        # Verify directories exist
        src_root = Path("src")
        assert src_root.exists(), "src directory should exist"
        
        subdirs = ["generators", "inference", "analysis"]
        for subdir in subdirs:
            dir_path = src_root / subdir
            assert dir_path.exists(), f"{subdir} directory should exist"
            assert dir_path.is_dir(), f"{subdir} should be a directory"
        
        # Verify __init__.py files exist
        for subdir in subdirs:
            init_path = src_root / subdir / "__init__.py"
            assert init_path.exists(), f"{subdir}/__init__.py should exist"
            assert init_path.is_file(), f"{subdir}/__init__.py should be a file"
            
    finally:
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """Test that running the script multiple times does not cause errors."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
        from setup_source_dirs import main
        
        # Run twice
        main()
        main()
        
        # Verify directories still exist and are valid
        src_root = Path("src")
        subdirs = ["generators", "inference", "analysis"]
        for subdir in subdirs:
            dir_path = src_root / subdir
            assert dir_path.exists()
            assert dir_path.is_dir()
            
    finally:
        os.chdir(original_cwd)