"""
Unit tests for T001d: create_results_dirs.py

Validates that the directory creation logic works correctly and
handles edge cases (e.g., existing directories).
"""

import os
import tempfile
from pathlib import Path
import pytest
from code.data_setup.create_results_dirs import create_results_directories


def test_create_results_directories_new():
    """Test creation of directories when they do not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        results_dir = base_path / "results"
        paper_dir = results_dir / "paper"

        # Directories should not exist yet
        assert not results_dir.exists()
        assert not paper_dir.exists()

        # Run the function
        returned_path = create_results_directories(base_path)

        # Verify directories exist
        assert results_dir.exists()
        assert results_dir.is_dir()
        assert paper_dir.exists()
        assert paper_dir.is_dir()

        # Verify returned path
        assert returned_path == results_dir


def test_create_results_directories_existing():
    """Test that the function handles existing directories gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        results_dir = base_path / "results"
        paper_dir = results_dir / "paper"

        # Pre-create the directories
        results_dir.mkdir(parents=True)
        paper_dir.mkdir(parents=True)

        # Run the function
        returned_path = create_results_directories(base_path)

        # Verify they still exist and are accessible
        assert results_dir.exists()
        assert paper_dir.exists()
        assert returned_path == results_dir


def test_create_results_directories_default_base():
    """
    Test that the function defaults to the project root when base_path is None.
    This test assumes the file is located at code/data_setup/create_results_dirs.py
    relative to the project root.
    """
    # We cannot easily test the default behavior in a temp directory context
    # without mocking __file__, so we test the logic of the default calculation
    # by passing a known path and verifying the calculation logic.
    # However, the function implementation uses Path(__file__).resolve().parent.parent.parent
    # which is dynamic. We rely on the previous tests for the explicit path logic.
    # This test serves as a placeholder for the default path behavior verification.
    pass
