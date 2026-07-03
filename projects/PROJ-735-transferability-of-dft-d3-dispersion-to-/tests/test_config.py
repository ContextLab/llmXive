"""
Tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import Config, get_config, set_seed, get_seed


class TestConfigInitialization:
    """Test config initialization and default values."""

    def test_config_singleton(self):
        """Test that config returns a singleton instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_default_seed(self):
        """Test that default seed is set correctly."""
        config = Config()
        # Should be 42 or from environment
        assert isinstance(config.seed, int)

    def test_path_resolution(self):
        """Test that paths are resolved correctly."""
        config = Config()
        assert config.data_dir is not None
        assert config.output_dir is not None
        assert config.logs_dir is not None

    def test_directories_created(self):
        """Test that required directories are created on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LLMXIVE_DATA_DIR"] = tmpdir
            os.environ["LLMXIVE_DATA_RAW_DIR"] = os.path.join(tmpdir, "raw")
            os.environ["LLMXIVE_DATA_DERIVED_DIR"] = os.path.join(tmpdir, "derived")
            os.environ["LLMXIVE_OUTPUT_DIR"] = os.path.join(tmpdir, "output")
            os.environ["LLMXIVE_LOGS_DIR"] = os.path.join(tmpdir, "logs")

            config = Config()

            assert Path(config.data_raw_dir).exists()
            assert Path(config.data_derived_dir).exists()
            assert Path(config.output_dir).exists()
            assert Path(config.logs_dir).exists()


class TestSeedManagement:
    """Test random seed management."""

    def test_set_seed(self):
        """Test setting the seed."""
        config = Config()
        config.set_seed(12345)
        assert config.seed == 12345

    def test_seed_affects_random(self):
        """Test that setting seed affects Python's random module."""
        config = Config()
        config.set_seed(42)
        val1 = random.random()

        config.set_seed(42)
        val2 = random.random()

        assert val1 == val2

    def test_seed_affects_numpy(self):
        """Test that setting seed affects NumPy's random state."""
        import numpy as np
        config = Config()
        config.set_seed(42)
        val1 = np.random.random()

        config.set_seed(42)
        val2 = np.random.random()

        assert val1 == val2

    def test_reset_seed(self):
        """Test resetting the seed."""
        config = Config()
        original_seed = config.seed
        config.set_seed(999)
        assert config.seed == 999
        config.reset_seed()
        # Should revert to original or environment
        assert config.seed == original_seed


class TestPathAccess:
    """Test path access methods."""

    def test_get_path(self):
        """Test getting paths by key."""
        config = Config()
        data_dir = config.get_path("data_dir")
        assert data_dir is not None
        assert isinstance(data_dir, Path)

    def test_get_path_invalid_key(self):
        """Test getting path with invalid key returns None."""
        config = Config()
        result = config.get_path("invalid_key_xyz")
        assert result is None

    def test_path_attributes(self):
        """Test that all expected path attributes exist."""
        config = Config()
        expected_attrs = [
            "data_dir", "data_raw_dir", "data_derived_dir",
            "output_dir", "logs_dir",
            "synthetic_xyz_zip", "synthetic_bulk_csv",
            "raw_energies_csv", "scaling_factor_txt",
            "benchmark_report_md", "correlation_report_md"
        ]
        for attr in expected_attrs:
            assert hasattr(config, attr)


class TestEnvironmentOverrides:
    """Test environment variable overrides."""

    def test_data_dir_override(self):
        """Test overriding data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LLMXIVE_DATA_DIR"] = tmpdir
            config = Config()
            assert str(config.data_dir) == tmpdir
            del os.environ["LLMXIVE_DATA_DIR"]

    def test_seed_override(self):
        """Test overriding seed via environment."""
        os.environ["LLMXIVE_RANDOM_SEED"] = "99999"
        config = Config()
        # Reset to trigger reload
        config.reset_seed()
        assert config.seed == 99999
        del os.environ["LLMXIVE_RANDOM_SEED"]


class TestValidation:
    """Test data file validation."""

    def test_validate_data_files_missing(self):
        """Test validation when files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LLMXIVE_DATA_DIR"] = tmpdir
            config = Config()
            is_valid, missing = config.validate_data_files()
            assert not is_valid
            assert len(missing) == 2  # Both files missing
            del os.environ["LLMXIVE_DATA_DIR"]

    def test_validate_data_files_present(self):
        """Test validation when files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LLMXIVE_DATA_DIR"] = tmpdir
            config = Config()

            # Create dummy files
            Path(config.synthetic_xyz_zip).touch()
            Path(config.synthetic_bulk_csv).touch()

            is_valid, missing = config.validate_data_files()
            assert is_valid
            assert len(missing) == 0
            del os.environ["LLMXIVE_DATA_DIR"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
