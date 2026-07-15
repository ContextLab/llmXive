"""Tests for directory setup functionality."""
import os
from pathlib import Path
import pytest

from setup_dirs import main


class TestDirectorySetup:
    """Test cases for the directory setup script."""

    def test_data_raw_exists(self):
        """Verify data/raw directory is created."""
        assert Path("data/raw").exists()
        assert Path("data/raw").is_dir()

    def test_data_processed_exists(self):
        """Verify data/processed directory is created."""
        assert Path("data/processed").exists()
        assert Path("data/processed").is_dir()

    def test_code_dataset_exists(self):
        """Verify code/dataset directory is created."""
        assert Path("code/dataset").exists()
        assert Path("code/dataset").is_dir()

    def test_code_agent_exists(self):
        """Verify code/agent directory is created."""
        assert Path("code/agent").exists()
        assert Path("code/agent").is_dir()

    def test_code_analysis_exists(self):
        """Verify code/analysis directory is created."""
        assert Path("code/analysis").exists()
        assert Path("code/analysis").is_dir()

    def test_tests_unit_exists(self):
        """Verify tests/unit directory is created."""
        assert Path("tests/unit").exists()
        assert Path("tests/unit").is_dir()

    def test_tests_integration_exists(self):
        """Verify tests/integration directory is created."""
        assert Path("tests/integration").exists()
        assert Path("tests/integration").is_dir()

    def test_unit_package_marker_exists(self):
        """Verify tests/unit/__init__.py exists."""
        assert Path("tests/unit/__init__.py").exists()

    def test_integration_package_marker_exists(self):
        """Verify tests/integration/__init__.py exists."""
        assert Path("tests/integration/__init__.py").exists()
