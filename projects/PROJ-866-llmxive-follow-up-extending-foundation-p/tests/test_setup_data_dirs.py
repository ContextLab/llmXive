import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path so we can import setup_data_dirs
# Assuming tests are run from root or we adjust path dynamically
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_data_dirs import create_data_directories

def test_create_directories_creates_all_required():
    """Test that create_data_directories creates all required paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            created = create_data_directories()
            
            # Verify all expected directories exist
            expected_dirs = [
                "code",
                "data",
                "data/raw",
                "data/processed",
                "data/results",
                "tests",
                "state",
                "state/projects",
                "contracts"
            ]
            
            for d in expected_dirs:
                full_path = Path(tmpdir) / d
                assert full_path.exists(), f"Directory {d} was not created"
                assert full_path.is_dir(), f"Path {d} is not a directory"
            
            # Verify return value contains the created paths
            assert len(created) == len(expected_dirs)
            
        finally:
            os.chdir(original_cwd)

def test_create_directories_idempotent():
    """Test that running the function twice doesn't raise errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            # First run
            create_data_directories()
            # Second run
            create_data_directories()
            # Third run
            create_data_directories()
            
            # Should still exist
            assert (Path(tmpdir) / "code").exists()
            assert (Path(tmpdir) / "data/raw").exists()
            
        finally:
            os.chdir(original_cwd)
