"""
Unit tests for setup_project.py
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import shutil

# Add parent directory to path to import setup_project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_project import create_directories


class TestSetupProject:
    """Tests for the project setup functionality."""

    def test_directories_created(self, tmp_path):
        """Test that all required directories are created."""
        # Create a temporary directory to act as the project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create the 'code' directory to match the expected structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            os.chdir(code_dir)

            # Run the function
            created_count = create_directories()

            # Verify directories exist
            assert (code_dir / "src").exists()
            assert (code_dir / "tests").exists()
            assert (code_dir / "data").exists()
            assert (code_dir / "data" / "raw").exists()
            assert (code_dir / "data" / "processed").exists()
            assert (code_dir / "results").exists()
            assert (code_dir / "figures").exists()
            assert (code_dir / "specs").exists()

            # Verify __init__.py files exist
            assert (code_dir / "src" / "__init__.py").exists()
            assert (code_dir / "tests" / "__init__.py").exists()
            assert (code_dir / "src" / "utils" / "__init__.py").exists()
            assert (code_dir / "tests" / "unit" / "__init__.py").exists()

        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Test that running the function twice does not cause errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            os.chdir(code_dir)

            # Run twice
            create_directories()
            count_second = create_directories()

            # Second run should create 0 new directories
            assert count_second == 0

        finally:
            os.chdir(original_cwd)