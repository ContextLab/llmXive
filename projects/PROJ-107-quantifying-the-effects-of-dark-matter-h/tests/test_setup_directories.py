"""
Tests for the project directory setup script.
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_directories import create_project_structure

class TestProjectStructure:
    """Tests for project directory creation."""

    def test_creates_required_root_directories(self, tmp_path):
        """Test that all required root directories are created."""
        # Temporarily change the working directory to tmp_path
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Mock the Path(__file__).resolve().parent.parent to point to tmp_path
            # by creating a dummy script structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            dummy_file = code_dir / "setup_directories.py"
            dummy_file.write_text("pass")
            
            # Run the function
            result = create_project_structure()
            
            # Verify root directories exist
            assert (tmp_path / "code").exists()
            assert (tmp_path / "data").exists()
            assert (tmp_path / "outputs").exists()
            assert (tmp_path / "docs").exists()
            assert (tmp_path / "state").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_creates_code_subdirectories(self, tmp_path):
        """Test that code subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create dummy structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            (tmp_path / "code" / "setup_directories.py").write_text("pass")
            
            create_project_structure()
            
            # Verify code subdirectories
            assert (tmp_path / "code" / "utils").exists()
            assert (tmp_path / "code" / "ingestion").exists()
            assert (tmp_path / "code" / "processing").exists()
            assert (tmp_path / "code" / "analysis").exists()
            assert (tmp_path / "code" / "tests").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_creates_data_subdirectories(self, tmp_path):
        """Test that data subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create dummy structure
            (tmp_path / "code").mkdir()
            (tmp_path / "code" / "setup_directories.py").write_text("pass")
            
            create_project_structure()
            
            # Verify data subdirectories
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "raw" / "millennium").exists()
            assert (tmp_path / "data" / "processed").exists()
            assert (tmp_path / "data" / "processed" / "matched_chunks").exists()
            assert (tmp_path / "data" / "metadata").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_creates_outputs_subdirectories(self, tmp_path):
        """Test that outputs subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create dummy structure
            (tmp_path / "code").mkdir()
            (tmp_path / "code" / "setup_directories.py").write_text("pass")
            
            create_project_structure()
            
            # Verify outputs subdirectories
            assert (tmp_path / "outputs" / "reports").exists()
            assert (tmp_path / "outputs" / "figures").exists()
            
        finally:
            os.chdir(original_cwd)
