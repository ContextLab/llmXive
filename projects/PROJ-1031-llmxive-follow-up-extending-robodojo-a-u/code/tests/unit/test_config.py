"""
Unit tests for the configuration module (config.py).
"""
import pytest
import os
from pathlib import Path
import sys

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

from config import (
    _PROJECT_ROOT,
    _CODE_ROOT,
    _DATA_ROOT,
    DATA_INTERIM,
    DATA_PROCESSED,
    ROBODOJO_DATASET_COMMIT,
    ROBODOJO_DATASET_NAME,
    RANDOM_SEED,
    MAX_RAM_GB,
    DEFAULT_DEVICE,
    get_path,
    get_data_path,
    validate_environment
)

class TestConfigConstants:
    """Tests for constant values defined in config."""

    def test_project_root_is_absolute(self):
        """Ensure project root is an absolute path."""
        assert _PROJECT_ROOT.is_absolute()

    def test_data_directories_exist(self):
        """Ensure data directories exist (created by config init)."""
        assert DATA_INTERIM.exists()
        assert DATA_PROCESSED.exists()
        assert _DATA_ROOT.exists()

    def test_robodojo_commit_hash(self):
        """Verify the specific commit hash for RoboDojo v3.0.1."""
        assert ROBODOJO_DATASET_COMMIT == "v3.0.1"

    def test_robodojo_dataset_name(self):
        """Verify the dataset name."""
        assert isinstance(ROBODOJO_DATASET_NAME, str)
        assert len(ROBODOJO_DATASET_NAME) > 0

    def test_random_seed(self):
        """Verify random seed is set."""
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED > 0

    def test_ram_limit(self):
        """Verify RAM limit is set to 6GB."""
        assert MAX_RAM_GB == 6.0

    def test_default_device(self):
        """Verify default device is CPU."""
        assert DEFAULT_DEVICE == "cpu"

class TestPathHelpers:
    """Tests for path helper functions."""

    def test_get_path_resolves_correctly(self):
        """Test get_path returns correct absolute path."""
        test_rel = "data/test_file.txt"
        result = get_path(test_rel)
        expected = _PROJECT_ROOT / test_rel
        assert result == expected.resolve()
        assert result.is_absolute()

    def test_get_data_path_resolves_correctly(self):
        """Test get_data_path returns correct absolute path under data root."""
        test_rel = "test_file.txt"
        result = get_data_path(test_rel)
        expected = _DATA_ROOT / test_rel
        assert result == expected.resolve()
        assert result.is_absolute()

class TestValidation:
    """Tests for environment validation."""

    def test_validate_environment_passes(self):
        """Ensure validation passes in a standard environment."""
        # This should not raise
        try:
            validate_environment()
        except Exception as e:
            pytest.fail(f"validate_environment raised unexpected exception: {e}")