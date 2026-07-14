"""
Unit tests to verify the project directory structure exists as expected.

These tests validate that T001a has successfully created the required
folder hierarchy.
"""

import os
import pytest
from pathlib import Path


@pytest.fixture
def root_dir():
    """Return the project root directory (parent of tests/)."""
    return Path(__file__).parent.parent


@pytest.fixture
def required_dirs(root_dir):
    """List of required directory paths relative to root."""
    return [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/processed/analysis",
        "logs"
    ]


class TestDirectoryStructure:
    """Tests for verifying the project directory structure."""

    def test_all_directories_exist(self, root_dir, required_dirs):
        """Assert that all required directories exist."""
        for rel_path in required_dirs:
            full_path = root_dir / rel_path
            assert full_path.exists(), f"Directory missing: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"

    def test_nested_data_directories(self, root_dir):
        """Assert that specific nested data directories exist."""
        processed_analysis = root_dir / "data" / "processed" / "analysis"
        assert processed_analysis.exists()
        assert processed_analysis.is_dir()

    def test_logs_directory_exists(self, root_dir):
        """Assert that the logs directory exists."""
        logs_dir = root_dir / "logs"
        assert logs_dir.exists()
        assert logs_dir.is_dir()