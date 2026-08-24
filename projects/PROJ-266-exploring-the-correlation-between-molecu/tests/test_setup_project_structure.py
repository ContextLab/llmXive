import os
import tempfile
from pathlib import Path

def test_create_directory_structure():
    """Test that the directory structure is created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Mock the function to use our temp dir
        from setup_project_structure import create_directory_structure
        create_directory_structure(root)

        assert (root / "code").is_dir(), "code/ directory should exist"
        assert (root / "tests").is_dir(), "tests/ directory should exist"
        assert (root / "data").is_dir(), "data/ directory should exist"