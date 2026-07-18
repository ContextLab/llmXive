"""
Test module for T036: Verification of output artifacts.
This test ensures that the verify_outputs.py script correctly identifies
missing or empty files.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from verify_outputs import verify_artifact

class TestT036Verification:
    def test_verify_existing_non_empty_file(self, tmp_path):
        """Test that a file that exists and has content returns True."""
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake image content")
        
        assert verify_artifact(test_file, "Test file") is True

    def test_verify_missing_file(self, tmp_path):
        """Test that a missing file returns False."""
        test_file = tmp_path / "nonexistent.png"
        
        assert verify_artifact(test_file, "Missing file") is False

    def test_verify_empty_file(self, tmp_path):
        """Test that an empty file returns False."""
        test_file = tmp_path / "empty.png"
        test_file.write_bytes(b"")
        
        assert verify_artifact(test_file, "Empty file") is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])