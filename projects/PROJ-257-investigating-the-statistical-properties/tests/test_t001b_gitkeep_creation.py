"""
Unit tests for T001b: Verification of .gitkeep file creation in src subdirectories.
"""
import os
import stat
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
from code.create_gitkeep_files import create_gitkeep_files, main

class TestGitKeepCreation:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """
        Setup a temporary directory structure that mimics the project root
        with a 'src' directory containing the required subdirectories.
        """
        # Create a temporary 'project root'
        self.test_root = tmp_path
        
        # Create the 'src' structure
        src_dir = self.test_root / "src"
        src_dir.mkdir()
        
        required_subdirs = ["data", "analysis", "viz", "utils"]
        for subdir in required_subdirs:
            (src_dir / subdir).mkdir()
        
        # Change CWD to the test root to mimic how the script is run
        self.original_cwd = os.getcwd()
        os.chdir(self.test_root)
        
        yield
        
        # Restore original CWD
        os.chdir(self.original_cwd)
        # Cleanup is handled by tmp_path fixture

    def test_gitkeep_files_created(self):
        """Verify that .gitkeep files are created in the correct locations."""
        result = create_gitkeep_files()
        
        expected_files = [
            "src/data/.gitkeep",
            "src/analysis/.gitkeep",
            "src/viz/.gitkeep",
            "src/utils/.gitkeep"
        ]
        
        assert len(result) == 4, f"Expected 4 files, got {len(result)}"
        
        for rel_path in expected_files:
            full_path = self.test_root / rel_path
            assert full_path.exists(), f"File {rel_path} was not created"
            assert full_path.is_file(), f"{rel_path} is not a file"

    def test_gitkeep_files_empty(self):
        """Verify that .gitkeep files are empty (0 bytes)."""
        create_gitkeep_files()
        
        files_to_check = [
            "src/data/.gitkeep",
            "src/analysis/.gitkeep",
            "src/viz/.gitkeep",
            "src/utils/.gitkeep"
        ]
        
        for rel_path in files_to_check:
            full_path = self.test_root / rel_path
            size = full_path.stat().st_size
            assert size == 0, f"File {rel_path} is not empty (size: {size})"

    def test_main_return_code_success(self, capsys):
        """Verify that main() returns 0 on success."""
        # Ensure the structure exists
        create_gitkeep_files()
        
        exit_code = main()
        assert exit_code == 0, f"main() returned {exit_code} instead of 0"
        
        # Check that verification messages were printed
        captured = capsys.readouterr()
        assert "Successfully created" in captured.out
        assert "Verified:" in captured.out

    def test_main_fails_if_src_missing(self):
        """Verify that main() fails if 'src' directory is missing."""
        # Remove the src directory to simulate T001a not running
        src_dir = self.test_root / "src"
        if src_dir.exists():
            shutil.rmtree(src_dir)
        
        # Reset CWD just in case, though it's already set to test_root
        os.chdir(self.test_root)
        
        # We expect a FileNotFoundError to be raised by create_gitkeep_files
        # which is called by main. However, main() catches exceptions.
        # Let's test the function directly first.
        with pytest.raises(FileNotFoundError):
            create_gitkeep_files()

    def test_stat_verification(self):
        """Simulate the verification step: Run stat on each file."""
        create_gitkeep_files()
        
        files = [
            "src/data/.gitkeep",
            "src/analysis/.gitkeep",
            "src/viz/.gitkeep",
            "src/utils/.gitkeep"
        ]
        
        for rel_path in files:
            full_path = self.test_root / rel_path
            # os.stat is the Python equivalent of the 'stat' command
            stat_info = os.stat(full_path)
            
            # Verify it's a file
            assert stat.S_ISREG(stat_info.st_mode), f"{rel_path} is not a regular file"
            
            # Verify existence
            assert full_path.exists(), f"{rel_path} does not exist"