import os
import tempfile
import shutil
from pathlib import Path

# We need to add the code directory to the path to import the module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import ensure_directory

def test_ensure_directory_creates_new_dir():
    """Test that ensure_directory creates a new directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = os.path.join(tmpdir, "test_new_dir")
        assert not os.path.exists(new_dir)
        
        ensure_directory(new_dir)
        
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)

def test_ensure_directory_existing_dir():
    """Test that ensure_directory does not fail on existing directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        existing_dir = os.path.join(tmpdir, "existing")
        os.makedirs(existing_dir)
        
        # Should not raise
        ensure_directory(existing_dir)
        
        assert os.path.exists(existing_dir)

def test_ensure_directory_nested():
    """Test that ensure_directory creates nested directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = os.path.join(tmpdir, "level1", "level2", "level3")
        assert not os.path.exists(nested_dir)
        
        ensure_directory(nested_dir)
        
        assert os.path.exists(nested_dir)
        assert os.path.isdir(nested_dir)
        assert os.path.exists(os.path.join(tmpdir, "level1"))
        assert os.path.exists(os.path.join(tmpdir, "level1", "level2"))