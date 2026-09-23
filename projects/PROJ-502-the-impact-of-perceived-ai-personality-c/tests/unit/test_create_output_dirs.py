"""
Unit tests for the create_output_dirs functionality.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from create_output_dirs import create_output_directories

def test_create_output_directories_creates_structure():
    """Test that the function creates the expected directory structure."""
    # Create a temporary directory to act as project root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_base = temp_path / "output"
        figures_dir = output_base / "figures"
        reports_dir = output_base / "reports"
        
        # Mock the project root by temporarily changing the working directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            # Create a dummy code directory to simulate project structure
            (temp_path / "code").mkdir()
            
            # Call the function
            create_output_directories()
            
            # Verify directories were created
            assert output_base.exists(), "output directory should exist"
            assert figures_dir.exists(), "output/figures directory should exist"
            assert reports_dir.exists(), "output/reports directory should exist"
            
            # Verify .gitkeep files were created
            assert (figures_dir / ".gitkeep").exists(), "figures/.gitkeep should exist"
            assert (reports_dir / ".gitkeep").exists(), "reports/.gitkeep should exist"
            
            # Verify they are directories
            assert figures_dir.is_dir(), "figures should be a directory"
            assert reports_dir.is_dir(), "reports should be a directory"
            
        finally:
            os.chdir(original_cwd)

def test_create_output_directories_idempotent():
    """Test that calling the function multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            (temp_path / "code").mkdir()
            
            # Call twice
            create_output_directories()
            create_output_directories()
            
            # Should still exist
            assert (temp_path / "output" / "figures").exists()
            assert (temp_path / "output" / "reports").exists()
            
        finally:
            os.chdir(original_cwd)
