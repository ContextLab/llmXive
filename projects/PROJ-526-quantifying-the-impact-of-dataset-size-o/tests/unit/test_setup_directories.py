import pytest
from pathlib import Path
import tempfile
import shutil
import os

# Import the functions to test
# Assuming the code is in code/setup_directories.py
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from setup_directories import create_directories

class TestCreateDirectories:
    def test_creates_single_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            dirs = ["test_dir"]
            create_directories(base, dirs)
            assert (base / "test_dir").is_dir()

    def test_creates_nested_directories(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            dirs = ["data/raw", "data/processed", "state"]
            create_directories(base, dirs)
            
            assert (base / "data").is_dir()
            assert (base / "data/raw").is_dir()
            assert (base / "data/processed").is_dir()
            assert (base / "state").is_dir()

    def test_handles_existing_directories(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            # Create one manually
            (base / "existing").mkdir()
            
            dirs = ["existing", "new_one"]
            create_directories(base, dirs) # Should not raise
            
            assert (base / "existing").is_dir()
            assert (base / "new_one").is_dir()