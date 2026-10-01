"""
Unit tests for the T056 placeholder verification script.
"""
import os
import tempfile
import pytest
from pathlib import Path
import subprocess
import sys

# Import the main logic if needed, or test via subprocess
from code.verify_placeholders import find_placeholders, pattern


def test_find_placeholders_empty():
    """Test that no matches are found in files without the placeholder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file without the placeholder
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("This is a normal file.\nNo placeholders here.")

        matches = find_placeholders(tmpdir, ["test.md"])
        assert matches == []

def test_find_placeholders_single_match():
    """Test that one match is found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("This has a [deferred] placeholder.\nAnd another line.")

        matches = find_placeholders(tmpdir, ["test.md"])
        assert len(matches) == 1
        assert matches[0][0].endswith("test.md")
        assert matches[0][1] == 1
        assert "[deferred]" in matches[0][2]

def test_find_placeholders_case_insensitive():
    """Test that [Deferred] and [DEFERRED] are also caught."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("Case 1: [Deferred]\nCase 2: [DEFERRED]\nCase 3: [deferred]")

        matches = find_placeholders(tmpdir, ["test.md"])
        assert len(matches) == 3

def test_find_placeholders_missing_file():
    """Test that missing files are handled gracefully (no error, no matches)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # File does not exist
        matches = find_placeholders(tmpdir, ["nonexistent.md"])
        assert matches == []

def test_script_exit_code_success():
    """Test that the script exits with 0 when no placeholders are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        Path(tmpdir, "plan.md").write_text("No placeholders.")
        Path(tmpdir, "spec.md").write_text("All resolved.")
        Path(tmpdir, "code").mkdir()
        Path(tmpdir, "code", "config.yaml").write_text("value: 1")

        # Run the script
        result = subprocess.run(
            [sys.executable, "code/verify_placeholders.py"],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "verification passed" in result.stdout.lower()

def test_script_exit_code_failure():
    """Test that the script exits with 1 when placeholders are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files with a placeholder
        Path(tmpdir, "plan.md").write_text("This is [deferred].")
        Path(tmpdir, "spec.md").write_text("All resolved.")
        Path(tmpdir, "code").mkdir()
        Path(tmpdir, "code", "config.yaml").write_text("value: 1")

        # Run the script
        result = subprocess.run(
            [sys.executable, "code/verify_placeholders.py"],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "found" in result.stdout.lower()
        assert "action required" in result.stdout.lower()