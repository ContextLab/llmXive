import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the setup_directories function.
# Since the project structure expects code/ at root, we add the parent to path if needed,
# but assuming this test runs from the project root, 'code' is a sibling.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_directories import setup_directories

def test_setup_directories_creates_structure():
    """Test that setup_directories creates the required folders."""
    # Create a temporary directory to act as a sandbox root
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run the setup
            created = setup_directories()
            
            # Verify the 'code' directory was created
            assert Path("code").exists(), "code/ directory should exist"
            assert Path("code").is_dir(), "code/ should be a directory"
            
            # Verify other standard directories created by the helper
            assert Path("data/raw").exists()
            assert Path("data/processed").exists()
            assert Path("results/plots").exists()
            assert Path("results/reports").exists()
            assert Path("tests/unit").exists()
            assert Path("tests/integration").exists()
            
            # Verify return value contains the code directory
            assert any("code" in p for p in created), "Return list should mention code dir"
        finally:
            os.chdir(original_cwd)

def test_setup_directories_idempotent():
    """Test that running setup again doesn't crash if dirs exist."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run once
            setup_directories()
            # Run again
            setup_directories()
            # Should not raise
            assert Path("code").exists()
        finally:
            os.chdir(original_cwd)