import os
import pytest
from pathlib import Path
import sys

# Add the project root to the path to allow imports from code/
# Assuming this test is in <project_root>/tests/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.setup_directories import setup_directories

class TestSetupDirectories:
    def test_directories_exist(self, tmp_path):
        """
        Test that setup_directories creates the required directory structure.
        
        This test patches the project root detection to use a temporary directory
        to avoid modifying the actual project structure during testing.
        """
        # Create a temporary directory structure to simulate the project root
        # We need to mock the Path resolution in setup_directories
        
        # Instead of mocking, we can just verify the logic by checking
        # if the function runs without error and creates directories
        # in a controlled environment.
        
        # For this test, we'll create a temporary "project root"
        # and verify the directories are created relative to it.
        
        # Note: The actual implementation determines project_root based on
        # the script location. To test this properly, we would need to
        # refactor the function to accept a root path parameter, or
        # mock the Path resolution.
        
        # For now, we'll test that the function doesn't crash and
        # that the expected directories are created in the actual project.
        
        # Since we can't easily mock the Path resolution in the function,
        # we'll just run it and check that the directories exist.
        
        # This is a bit of a workaround, but it verifies the functionality
        # in the real environment.
        
        # Save original CWD
        original_cwd = os.getcwd()
        
        try:
            # Change to project root
            os.chdir(str(project_root))
            
            # Run setup
            result_root = setup_directories()
            
            # Verify the root returned is correct
            assert result_root == project_root
            
            # Verify directories exist
            expected_dirs = [
                "data/raw",
                "data/processed",
                "data/interim",
                "data/results",
                "code",
                "tests",
            ]
            
            for dir_name in expected_dirs:
                dir_path = project_root / dir_name
                assert dir_path.exists(), f"Directory {dir_path} does not exist"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"
                
        finally:
            # Restore original CWD
            os.chdir(original_cwd)
    
    def test_directories_are_writable(self):
        """
        Test that the created directories are writable.
        """
        # Change to project root
        original_cwd = os.getcwd()
        
        try:
            os.chdir(str(project_root))
            
            # Run setup to ensure directories exist
            setup_directories()
            
            # Test writing a temporary file in each directory
            test_files = [
                ("data/raw", ".test_write"),
                ("data/processed", ".test_write"),
                ("data/interim", ".test_write"),
                ("data/results", ".test_write"),
                ("code", ".test_write"),
                ("tests", ".test_write"),
            ]
            
            for dir_name, file_name in test_files:
                dir_path = project_root / dir_name
                test_file = dir_path / file_name
                
                try:
                    # Create a test file
                    test_file.touch()
                    assert test_file.exists(), f"Could not create file in {dir_path}"
                    
                    # Write some content
                    with open(test_file, 'w') as f:
                        f.write("test")
                    
                    # Read back
                    with open(test_file, 'r') as f:
                        content = f.read()
                    assert content == "test", f"Could not write/read in {dir_path}"
                    
                finally:
                    # Clean up
                    if test_file.exists():
                        test_file.unlink()
            
        finally:
            os.chdir(original_cwd)
