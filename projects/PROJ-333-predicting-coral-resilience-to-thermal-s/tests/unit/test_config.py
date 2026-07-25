"""
Unit tests for configuration loading and path resolution.
"""
import os
import sys
from pathlib import Path
import pytest

# Adjust path to include project root if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import ensure_directories, get_thresholds

class TestConfig:
    def test_ensure_directories_creates_structure(self, tmp_path):
        """Test that ensure_directories creates the required folder structure."""
        # Mock the config to use a temporary directory
        import config
        original_base = config.PROJECT_ROOT
        config.PROJECT_ROOT = tmp_path

        try:
            ensure_directories()
            
            assert (tmp_path / "code").exists()
            assert (tmp_path / "tests").exists()
            assert (tmp_path / "data").exists()
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
            assert (tmp_path / "data" / "interim").exists()
            assert (tmp_path / "data" / "external").exists()
        finally:
            config.PROJECT_ROOT = original_base

    def test_get_thresholds_returns_dict(self):
        """Test that get_thresholds returns a dictionary with expected keys."""
        thresholds = get_thresholds()
        assert isinstance(thresholds, dict)
        assert "MIN_COUNT_THRESHOLD" in thresholds
        assert "MIN_SAMPLES_FOR_FILTER" in thresholds