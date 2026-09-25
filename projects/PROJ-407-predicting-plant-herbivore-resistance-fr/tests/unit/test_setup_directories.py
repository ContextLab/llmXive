import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# Since we are running this test inside the project root, we assume code/ is in path
# or we add the parent directory to sys.path if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_directories import ensure_directories

def test_ensure_directories_creates_missing():
    """Test that ensure_directories creates directories that do not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Ensure directories
            paths = ensure_directories()
            
            # Verify all paths exist
            for p in paths:
                assert os.path.isdir(p), f"Directory {p} was not created"
            
            # Verify specific required subdirectories exist
            required_subdirs = [
                "data/raw",
                "data/interim",
                "data/processed",
                "tests/unit",
                "tests/integration",
                "tests/contract"
            ]
            
            for subdir in required_subdirs:
                full_path = os.path.join(tmpdir, subdir)
                assert os.path.isdir(full_path), f"Required subdirectory {subdir} missing"
                
        finally:
            os.chdir(original_cwd)

def test_ensure_directories_idempotent():
    """Test that running ensure_directories twice does not cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # First run
            paths1 = ensure_directories()
            
            # Second run
            paths2 = ensure_directories()
            
            # Should return same number of paths
            assert len(paths1) == len(paths2)
            
            # All paths should still exist
            for p in paths2:
                assert os.path.isdir(p)
                
        finally:
            os.chdir(original_cwd)