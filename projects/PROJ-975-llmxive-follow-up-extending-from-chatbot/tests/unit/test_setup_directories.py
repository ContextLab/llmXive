import os
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# We need to import the function from the code module
# Since the project structure might not be fully set up in the test environment,
# we ensure the path is correct or mock the import if necessary.
# Assuming standard PYTHONPATH includes the root or 'code' is in path.
# For this test, we assume the test runner is configured to find 'code'.
from code.setup_directories import create_project_structure

class TestSetupDirectories:
    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        # Change to a temporary directory to avoid polluting the real project
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Mock os.makedirs to capture calls
            with patch('code.setup_directories.os.makedirs') as mock_makedirs:
                create_project_structure()
                
                expected_dirs = [
                    "data/raw",
                    "data/results",
                    "code",
                    "tests/unit",
                    "tests/contract",
                    "contracts",
                    "projects/PROJ-975-llmxive-follow-up-extending-from-chatbot"
                ]
                
                # Verify makedirs was called for each expected directory
                for dir_path in expected_dirs:
                    mock_makedirs.assert_any_call(dir_path, exist_ok=True)
                    
        finally:
            os.chdir(original_cwd)

    def test_directories_exist_after_run(self, tmp_path):
        """Test that directories actually exist on disk after running."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            create_project_structure()
            
            expected_dirs = [
                "data/raw",
                "data/results",
                "code",
                "tests/unit",
                "tests/contract",
                "contracts",
                "projects/PROJ-975-llmxive-follow-up-extending-from-chatbot"
            ]
            
            for dir_path in expected_dirs:
                assert os.path.isdir(dir_path), f"Directory {dir_path} was not created"
        finally:
            os.chdir(original_cwd)

    def test_idempotent(self, tmp_path):
        """Test that running the script twice does not raise errors."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Run twice
            create_project_structure()
            create_project_structure()
            
            # Verify directories still exist
            assert os.path.isdir("code")
            assert os.path.isdir("data/raw")
        finally:
            os.chdir(original_cwd)