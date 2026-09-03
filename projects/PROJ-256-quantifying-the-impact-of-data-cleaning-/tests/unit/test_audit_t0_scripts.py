"""
Unit tests for the audit_t0_scripts functionality.
"""
import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add the code/scripts directory to the path to import the audit function
# Assuming this test runs from the project root or the path is adjusted
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "scripts"))

from audit_t0_scripts import audit_t0_scripts

def test_audit_no_files():
    """Test when no t0*.py files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy non-matching file
        Path(tmpdir, "main.py").touch()
        Path(tmpdir, "utils.py").touch()
        
        result = audit_t0_scripts(tmpdir)
        assert result == []

def test_audit_with_files():
    """Test when t0*.py files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create matching and non-matching files
        Path(tmpdir, "t001_script.py").touch()
        Path(tmpdir, "t022_analysis.py").touch()
        Path(tmpdir, "t100_script.py").touch() # Should not match t0*
        Path(tmpdir, "main.py").touch()
        Path(tmpdir, "t099.py").touch()
        
        result = audit_t0_scripts(tmpdir)
        expected = ["t001_script.py", "t022_analysis.py", "t099.py"]
        assert sorted(result) == sorted(expected)

def test_audit_nonexistent_dir():
    """Test with a directory that does not exist."""
    result = audit_t0_scripts("nonexistent_directory_xyz")
    assert result == []