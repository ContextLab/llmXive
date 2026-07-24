import os
import tempfile
import pytest
from pathlib import Path

# Add parent to path for imports if running standalone
sys_path_len = len(__import__('sys').path)
try:
    __import__('sys').path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
    from utils.setup_dirs import setup_project_structure, ensure_directory
finally:
    # Restore path
    if len(__import__('sys').path) > sys_path_len:
        __import__('sys').path = __import__('sys').path[:sys_path_len]

def test_setup_creates_required_directories():
    """Test that setup_project_structure creates all required directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        setup_project_structure(root)
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/reports",
            "tests",
            "artifacts",
        ]
        
        for dir_path in required_dirs:
            full_path = root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_ensure_directory_creates_parent_dirs():
    """Test that ensure_directory creates parent directories if needed."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        deep_path = root / "a" / "b" / "c"
        
        ensure_directory(deep_path)
        
        assert deep_path.exists()
        assert deep_path.is_dir()

def test_ensure_directory_no_error_if_exists():
    """Test that ensure_directory does not raise if directory exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        existing_dir = root / "existing"
        existing_dir.mkdir()
        
        # Should not raise
        ensure_directory(existing_dir)
        
        assert existing_dir.exists()