import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the functions we are testing
# Assuming the test file is at tests/unit/test_directory_structure.py
# and the code is at code/setup_directories.py
# We need to add the parent of 'tests' to the path to import from 'code'
# OR import directly if the structure allows.
# Given the API surface: `from tests.unit.test_directory_structure import TestDirectoryStructure`
# The test file itself is the artifact. We import the implementation from code/.

# Adjust path to import from code directory if running from root
root_dir = Path(__file__).resolve().parent.parent.parent
code_dir = root_dir / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_directories import create_directories, verify_directories, generate_verification_log

class TestDirectoryStructure:
    
    def test_create_directories(self):
        """Test that directories are created successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            dirs = ["raw", "interim", "processed"]
            created = create_directories(base, dirs)
            
            assert len(created) == 3
            for p in created:
                assert p.exists()
                assert p.is_dir()

    def test_verify_directories(self):
        """Test that verification returns True for existing dirs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            dirs = ["test_dir"]
            created = create_directories(base, dirs)
            
            assert verify_directories(created) is True
            
            # Test with non-existent
            fake_path = base / "non_existent"
            assert verify_directories([fake_path]) is False

    def test_generate_verification_log(self):
        """Test that the verification log is created and contains expected content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            dirs = ["raw", "interim"]
            created = create_directories(base, dirs)
            
            log_path = base / "verify.log"
            generate_verification_log(created, log_path)
            
            assert log_path.exists()
            
            content = log_path.read_text()
            assert "Directory Verification Log" in content
            assert "Generated at:" in content
            assert "Path:" in content
            assert "Exists:" in content
            assert "Is Directory:" in content
            
            # Verify specific paths are mentioned
            for p in created:
                assert str(p) in content

    def test_full_workflow(self):
        """Simulate the full T001 workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            required = ["data/raw", "data/interim", "data/processed", "tests/unit", "tests/integration", "reports"]
            
            # Create
            created = create_directories(base, required)
            
            # Verify
            assert verify_directories(created)
            
            # Log
            log_file = base / "data" / ".verify_structure.log"
            generate_verification_log(created, log_file)
            
            assert log_file.exists()
            content = log_file.read_text()
            # Check for a few key directories in the log
            assert "data/raw" in content
            assert "reports" in content