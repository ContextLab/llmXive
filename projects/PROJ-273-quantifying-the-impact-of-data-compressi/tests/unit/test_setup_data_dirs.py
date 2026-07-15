import os
import shutil
import tempfile
from pathlib import Path
import sys

# Add code directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories

def test_setup_data_directories_creates_structure():
    """
    Test that setup_data_directories creates the required directories:
    data/raw, data/interim, data/processed
    """
    # Use a temporary directory to avoid polluting the actual project root
    # We will mock the Path behavior or run in a temp dir context.
    # Since the function hardcodes "data", we need to be careful.
    # For this unit test, we will create a temp dir, cd into it, run, and check.
    
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.chdir(temp_dir)
        
        # Run the function
        result = setup_data_directories()
        
        # Verify directories exist
        base = Path(temp_dir) / "data"
        assert (base / "raw").is_dir(), "data/raw directory not created"
        assert (base / "interim").is_dir(), "data/interim directory not created"
        assert (base / "processed").is_dir(), "data/processed directory not created"
        
        # Verify .gitkeep files exist
        assert (base / "raw" / ".gitkeep").is_file(), "data/raw/.gitkeep not created"
        assert (base / "interim" / ".gitkeep").is_file(), "data/interim/.gitkeep not created"
        assert (base / "processed" / ".gitkeep").is_file(), "data/processed/.gitkeep not created"
        
        # Verify return value contains the paths
        assert len(result) == 6, f"Expected 6 items in return (3 dirs + 3 gitkeeps), got {len(result)}"
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

def test_setup_data_directories_idempotent():
    """
    Test that running setup_data_directories multiple times does not raise errors
    and handles existing directories gracefully.
    """
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.chdir(temp_dir)
        
        # Run once
        setup_data_directories()
        
        # Run again
        result = setup_data_directories()
        
        # Should still have the directories
        base = Path(temp_dir) / "data"
        assert (base / "raw").is_dir()
        assert (base / "interim").is_dir()
        assert (base / "processed").is_dir()
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)