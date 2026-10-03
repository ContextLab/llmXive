import os
import tempfile
from pathlib import Path
import pytest

# Mock the logging setup to avoid conflicts in test environment
import sys
from unittest.mock import patch

# Ensure we can import from the project root
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.mkdirs import ensure_dirs

def test_ensure_dirs_creates_new_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "new_dir" / "sub_dir"
        assert not target_dir.exists()
        
        ensure_dirs([str(target_dir)])
        
        assert target_dir.exists()
        assert target_dir.is_dir()

def test_ensure_dirs_skips_existing_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "existing_dir"
        target_dir.mkdir(parents=True)
        assert target_dir.exists()
        
        # Should not raise an error
        ensure_dirs([str(target_dir)])
        
        assert target_dir.exists()

def test_ensure_dirs_multiple_paths():
    with tempfile.TemporaryDirectory() as tmpdir:
        dir1 = Path(tmpdir) / "dir1"
        dir2 = Path(tmpdir) / "dir2" / "nested"
        
        ensure_dirs([str(dir1), str(dir2)])
        
        assert dir1.exists()
        assert dir2.exists()