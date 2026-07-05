import os
import tempfile
import shutil
import pytest

# Adjust import to work within the project structure
# We will test the logic by importing the function and mocking the path
import sys
from unittest.mock import patch, MagicMock

def test_create_directories_structure():
    """
    Test that create_directories creates the expected directory structure.
    """
    # Import the function
    from code.setup_directories import create_directories

    # Create a temporary directory to act as project root
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock os.path.dirname to return our temp_dir as the project root
        # and ensure the script thinks it's in code/setup_directories.py
        original_dirname = os.path.dirname

        def mock_dirname(path):
            if 'setup_directories.py' in path:
                return temp_dir
            return original_dirname(path)

        with patch('os.path.dirname', side_effect=mock_dirname):
            with patch('os.path.abspath', side_effect=lambda x: os.path.join(temp_dir, x) if not os.path.isabs(x) else x):
                # Run the function
                success = create_directories()

                # Verify success
                assert success is True, "Directory creation should succeed"

                # Verify directories exist
                expected_dirs = [
                    os.path.join(temp_dir, 'code'),
                    os.path.join(temp_dir, 'code', 'utils'),
                    os.path.join(temp_dir, 'code', 'models'),
                    os.path.join(temp_dir, 'code', 'tests'),
                ]

                for dir_path in expected_dirs:
                    assert os.path.isdir(dir_path), f"Directory {dir_path} should exist"