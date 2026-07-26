"""
Unit tests for src/lib/config.py configuration module.
"""
import os
import sys
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root))

from src.lib import config


class TestConfigConstants:
    """Tests for configuration constants."""

    def test_random_seed_is_integer(self):
        """Verify RANDOM_SEED is an integer."""
        assert isinstance(config.RANDOM_SEED, int)
        assert config.RANDOM_SEED == 42

    def test_memory_limit_is_positive(self):
        """Verify MEMORY_LIMIT_GB is a positive float."""
        assert isinstance(config.MEMORY_LIMIT_GB, float)
        assert config.MEMORY_LIMIT_GB > 0
        assert config.MEMORY_LIMIT_GB == 7.0

    def test_timeout_is_positive(self):
        """Verify GLOBAL_TIMEOUT_SECONDS is a positive integer."""
        assert isinstance(config.GLOBAL_TIMEOUT_SECONDS, int)
        assert config.GLOBAL_TIMEOUT_SECONDS > 0
        assert config.GLOBAL_TIMEOUT_SECONDS == 300

    def test_min_sample_size(self):
        """Verify MIN_SAMPLE_SIZE meets FR-010 requirement (>= 30)."""
        assert config.MIN_SAMPLE_SIZE >= 30
        assert config.MIN_SAMPLE_SIZE == 30

    def test_auc_threshold(self):
        """Verify AUC_ROC_THRESHOLD is a valid probability."""
        assert 0.0 <= config.AUC_ROC_THRESHOLD <= 1.0
        assert config.AUC_ROC_THRESHOLD == 0.65


class TestConfigPaths:
    """Tests for path resolution and directory existence."""

    def test_project_root_exists(self):
        """Verify PROJECT_ROOT points to a valid directory."""
        assert isinstance(config.PROJECT_ROOT, Path)
        assert config.PROJECT_ROOT.exists()

    def test_data_dir_exists(self):
        """Verify DATA_DIR exists or was created."""
        assert config.DATA_DIR.exists()
        assert config.DATA_DIR.is_dir()

    def test_figures_dir_exists(self):
        """Verify FIGURES_DIR exists or was created."""
        assert config.FIGURES_DIR.exists()
        assert config.FIGURES_DIR.is_dir()

    def test_state_dir_exists(self):
        """Verify STATE_DIR exists or was created."""
        assert config.STATE_DIR.exists()
        assert config.STATE_DIR.is_dir()

    def test_get_path_resolution(self):
        """Verify get_path correctly resolves relative paths."""
        test_rel_path = "test/subdir"
        resolved = config.get_path(test_rel_path)
        expected = config.PROJECT_ROOT / test_rel_path
        assert resolved == expected
        assert resolved.is_absolute()


class TestConfigFunctions:
    """Tests for helper functions."""

    def test_ensure_dirs_idempotent(self):
        """Verify ensure_dirs can be called multiple times without error."""
        # First call creates dirs (side effect of import)
        config.ensure_dirs()
        # Second call should not raise
        config.ensure_dirs()

    def test_memory_limit_bytes_calculation(self):
        """Verify MEMORY_LIMIT_BYTES is correctly calculated from GB."""
        expected_bytes = int(7.0 * 1024**3)
        assert config.MEMORY_LIMIT_BYTES == expected_bytes