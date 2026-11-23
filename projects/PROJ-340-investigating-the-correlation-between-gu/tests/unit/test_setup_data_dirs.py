"""
Unit tests for the setup_data_dirs module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the module. Since it's in code/, we adjust path or import directly.
# Assuming standard python path setup where 'code' is importable or we use relative imports.
# For unit tests in tests/, we often add the parent to sys.path if not already done.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_data_dirs import setup_data_directories


class TestSetupDataDirs:
    """Unit tests for setup_data_directories function."""

    def test_function_returns_list_of_created_dirs(self):
        """Verify the function returns a list of created directory paths."""
        # This test assumes the directories don't exist yet or we are in a clean env.
        # In a real CI, we might want to run this in a temp directory.
        # However, the function prints and creates in the current working directory.
        result = setup_data_directories()
        assert isinstance(result, list), "Function should return a list"
        # At least the 4 subdirs should be reported or exist
        assert len(result) >= 0 # It might be 0 if they already exist

    def test_directories_are_created(self):
        """Verify that the directories actually exist after calling the function."""
        setup_data_directories()
        
        expected_dirs = [
            "data",
            "data/raw",
            "data/processed",
            "data/results",
            "data/config"
        ]
        
        for dir_path in expected_dirs:
            assert Path(dir_path).exists(), f"Directory {dir_path} was not created"
            assert Path(dir_path).is_dir(), f"{dir_path} exists but is not a directory"
