"""
Unit tests for setup_data_dirs.py
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories

def test_setup_data_directories_creates_dirs():
    """Test that setup_data_directories creates the required directories."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Mock the project root by temporarily changing the working directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create a dummy code directory structure to match the script's expectation
            code_dir = tmpdir_path / "code"
            code_dir.mkdir(exist_ok=True)
            (code_dir / "__init__.py").touch()
            
            # Run the function
            setup_data_directories()
            
            # Verify directories were created
            data_dir = tmpdir_path / "data"
            raw_dir = data_dir / "raw"
            processed_dir = data_dir / "processed"
            
            assert data_dir.exists(), "data directory should exist"
            assert raw_dir.exists(), "data/raw directory should exist"
            assert processed_dir.exists(), "data/processed directory should exist"
            
            # Verify .gitkeep files were created
            assert (raw_dir / ".gitkeep").exists(), "data/raw/.gitkeep should exist"
            assert (processed_dir / ".gitkeep").exists(), "data/processed/.gitkeep should exist"
            
        finally:
            os.chdir(original_cwd)

def test_setup_data_directories_idempotent():
    """Test that running setup_data_directories multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        original_cwd = os.getcwd()
        
        try:
            os.chdir(tmpdir)
            code_dir = tmpdir_path / "code"
            code_dir.mkdir(exist_ok=True)
            (code_dir / "__init__.py").touch()
            
            # Run twice
            setup_data_directories()
            setup_data_directories()
            
            # Verify still exists
            data_dir = tmpdir_path / "data"
            assert data_dir.exists()
            assert (data_dir / "raw").exists()
            assert (data_dir / "processed").exists()
            
        finally:
            os.chdir(original_cwd)
