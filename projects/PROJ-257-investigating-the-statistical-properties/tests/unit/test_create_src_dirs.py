import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from create_src_dirs import create_directories, main

class TestCreateSrcDirs:
    def test_creates_src_directory(self, tmp_path):
        """Test that the src directory is created."""
        # Change to temp directory to avoid polluting real repo
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            src_dir, subdirs = create_directories()
            assert src_dir.exists()
            assert src_dir.is_dir()
            assert src_dir.name == "src"
        finally:
            os.chdir(original_cwd)

    def test_creates_required_subdirectories(self, tmp_path):
        """Test that all required subdirectories are created."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            src_dir, subdirs = create_directories()
            
            expected_subdirs = {"data", "analysis", "viz", "utils"}
            assert set(subdirs) == expected_subdirs
            
            for subdir in expected_subdirs:
                subdir_path = src_dir / subdir
                assert subdir_path.exists()
                assert subdir_path.is_dir()
        finally:
            os.chdir(original_cwd)

    def test_creates_gitkeep_in_src(self, tmp_path):
        """Test that .gitkeep is created in src/ directory."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            src_dir, _ = create_directories()
            gitkeep_path = src_dir / ".gitkeep"
            assert gitkeep_path.exists()
            assert gitkeep_path.is_file()
        finally:
            os.chdir(original_cwd)

    def test_creates_gitkeep_in_subdirectories(self, tmp_path):
        """Test that .gitkeep is created in each subdirectory."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            src_dir, subdirs = create_directories()
            
            for subdir in subdirs:
                subdir_path = src_dir / subdir
                gitkeep_path = subdir_path / ".gitkeep"
                assert gitkeep_path.exists()
                assert gitkeep_path.is_file()
        finally:
            os.chdir(original_cwd)

    def test_main_function(self, tmp_path):
        """Test that main() runs without error and verifies structure."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # This should not raise an exception
            main()
            
            # Verify the structure exists
            src_dir = Path("src")
            assert src_dir.exists()
            
            expected_dirs = {"analysis", "data", "utils", "viz"}
            actual_dirs = {p.name for p in src_dir.iterdir() if p.is_dir()}
            assert actual_dirs == expected_dirs
        finally:
            os.chdir(original_cwd)

    def test_directory_list_matches_verification(self, tmp_path):
        """
        Test that the directory listing matches the verification requirement:
        'ls src/' should return [data, analysis, viz, utils] (order may vary).
        """
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            src_dir, _ = create_directories()
            
            # Simulate 'ls src/'
            contents = sorted([p.name for p in src_dir.iterdir() if p.is_dir()])
            
            # The task requires these specific subdirectories
            expected = ["analysis", "data", "utils", "viz"]
            assert contents == expected
        finally:
            os.chdir(original_cwd)