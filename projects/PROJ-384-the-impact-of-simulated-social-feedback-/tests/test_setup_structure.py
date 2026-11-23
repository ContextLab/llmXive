import os
import tempfile
from pathlib import Path
import pytest
import shutil

# We need to import from code/setup_structure.py
# Adjusting sys.path to allow importing from code/
import sys
from pathlib import Path

# Add the 'code' directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_structure import create_directories

class TestDirectoryCreation:
    def test_creates_required_directories(self, tmp_path):
        """
        Verify that create_directories creates the required structure:
        code/, code/utils/, tests/, data/raw/, data/processed/
        """
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the function
            create_directories()
            
            # Verify existence
            assert (tmp_path / "code").is_dir(), "Directory 'code' missing"
            assert (tmp_path / "code" / "utils").is_dir(), "Directory 'code/utils' missing"
            assert (tmp_path / "tests").is_dir(), "Directory 'tests' missing"
            assert (tmp_path / "data" / "raw").is_dir(), "Directory 'data/raw' missing"
            assert (tmp_path / "data" / "processed").is_dir(), "Directory 'data/processed' missing"
            
            # Verify additional expected directories from the implementation
            assert (tmp_path / "logs").is_dir(), "Directory 'logs' missing"
            assert (tmp_path / "data" / "raw" / "lexicons").is_dir(), "Directory 'data/raw/lexicons' missing"
            
        finally:
            os.chdir(original_cwd)

    def test_idempotent(self, tmp_path):
        """
        Verify that running create_directories twice does not raise errors
        and does not duplicate content (directories remain single).
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            create_directories()
            create_directories() # Run again
            
            # Should still exist and be a directory
            assert (tmp_path / "code").is_dir()
            assert (tmp_path / "data" / "raw").is_dir()
            
        finally:
            os.chdir(original_cwd)
