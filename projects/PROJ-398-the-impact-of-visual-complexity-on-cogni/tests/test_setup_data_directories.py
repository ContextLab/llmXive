"""
Unit tests for ``code/setup_data_directories.py``.

The tests verify that ``ensure_directory`` correctly creates a directory
without raising and that ``main`` can be called without error (the actual
creation of the project‑wide ``data/`` hierarchy is exercised but does not
interfere with the repository because the test runs in an isolated temporary
directory).
"""

import os
import tempfile
from pathlib import Path

import pytest

# Import the functions from the module under test.
from setup_data_directories import ensure_directory, main

def test_ensure_directory_creates_path():
    """``ensure_directory`` must create a missing directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "nested" / "dir"
        # Directory should not exist yet.
        assert not target.exists()
        # Call the helper.
        result = ensure_directory(target)
        # It should now exist and be a directory.
        assert result.is_dir()
        assert result == target.resolve()

def test_main_creates_default_data_structure(tmp_path, monkeypatch, capsys):
    """
    ``main`` should create the four top‑level ``data/*`` directories.
    The test runs in a temporary directory that mimics a project root.
    """
    # Monkey‑patch the location of the project root to the temporary path.
    # ``setup_data_directories`` computes the base as two parents up from this file.
    # We therefore place a dummy ``code`` package inside the temporary directory
    # and adjust ``__file__`` accordingly.
    dummy_code_dir = tmp_path / "code"
    dummy_code_dir.mkdir()
    dummy_file = dummy_code_dir / "setup_data_directories.py"
    dummy_file.write_text("# placeholder – not executed")
    monkeypatch.setattr("setup_data_directories.__file__", str(dummy_file))

    # Run ``main`` – it will resolve the base directory relative to the patched file.
    main()

    # Capture printed output to ensure the function ran.
    captured = capsys.readouterr()
    assert "Created/verified data directory" in captured.out

    # Verify that the expected directories now exist under the temporary project root.
    base_data = tmp_path / "data"
    expected_dirs = [
        base_data / "stimuli",
        base_data / "processed",
        base_data / "measurements",
        base_data / "raw",
    ]
    for d in expected_dirs:
        assert d.is_dir()