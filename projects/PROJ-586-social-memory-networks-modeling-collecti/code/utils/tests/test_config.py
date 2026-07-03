"""
Tests for code/utils/config.py — environment management and configuration.
"""

import pytest
import tempfile
from pathlib import Path
from utils.config import Config, load_config, save_config, ensure_config_file, get_config


class TestConfigDefaults:
    """Test that Config dataclass has correct defaults."""

    def test_default_seed(self):
        """Verify default seed is 42."""
        config = Config()
        assert config.seed == 42

    def test_default_device(self):
        """Verify default device is 'cpu'."""
        config = Config()
        assert config.device == "cpu"

    def test_default_model_name(self):
        """Verify default model name is set."""
        config = Config()
        assert config.model_name == "facebook/opt-125m"

    def test_default_dtype(self):
        """Verify default dtype is float32."""
        config = Config()
        assert config.dtype == "float32"

    def test_default_log_file(self):
        """Verify default log file is experiment.log."""
        config = Config()
        assert config.log_file == "experiment.log"

    def test_default_output_dir(self):
        """Verify default output directory is results."""
        config = Config()
        assert config.output_dir == "results"

    def test_default_data_dir(self):
        """Verify default data directory is data."""
        config = Config()
        assert config.data_dir == "data"

    def test_default_num_games_full(self):
        """Verify default num_games_full is 1000."""
        config = Config()
        assert config.num_games_full == 1000

    def test_default_num_games_limited(self):
        """Verify default num_games_limited is 1000."""
        config = Config()
        assert config.num_games_limited == 1000

    def test_default_agent_counts(self):
        """Verify default agent counts are [3, 5, 7]."""
        config = Config()
        assert config.agent_counts == [3, 5, 7]

    def test_default_context_windows(self):
        """Verify default context windows are [128, 256, 512]."""
        config = Config()
        assert config.context_windows == [128, 256, 512]


class TestLoadConfigDefaults:
    """Test load_config with missing file."""

    def test_load_nonexistent_file(self):
        """Verify load_config returns defaults when file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.yaml"
            config = load_config(str(config_path))
            assert config.seed == 42
            assert config.device == "cpu"
            assert config.model_name == "facebook/opt-125m"


class TestSaveAndLoadConfig:
    """Test save_config and load_config round-trip."""

    def test_save_and_load_yaml(self):
        """Verify save_config and load_config preserve values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            # Create and save a custom config
            original = Config(
                seed=123,
                device="cuda",
                model_name="gpt2",
                num_games_full=500
            )
            save_config(original, str(config_path))
            
            # Load it back
            loaded = load_config(str(config_path))
            
            # Verify critical fields
            assert loaded.seed == 123
            assert loaded.device == "cuda"
            assert loaded.model_name == "gpt2"
            assert loaded.num_games_full == 500
            # Defaults for unspecified fields
            assert loaded.dtype == "float32"

    def test_save_and_load_with_lists(self):
        """Verify list fields are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            original = Config(
                agent_counts=[2, 4, 6, 8],
                context_windows=[64, 128, 256]
            )
            save_config(original, str(config_path))
            
            loaded = load_config(str(config_path))
            assert loaded.agent_counts == [2, 4, 6, 8]
            assert loaded.context_windows == [64, 128, 256]


class TestEnsureConfigFile:
    """Test ensure_config_file creates file if missing."""

    def test_ensure_creates_file(self):
        """Verify ensure_config_file creates config.yaml with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                config_path = ensure_config_file()
                assert config_path.exists()
                assert config_path.name == "config.yaml"
                
                # Verify it has the right defaults
                loaded = load_config()
                assert loaded.seed == 42
                assert loaded.device == "cpu"
            finally:
                os.chdir(original_cwd)

    def test_ensure_does_not_overwrite(self):
        """Verify ensure_config_file does not overwrite existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            # Create a custom config
            custom = Config(seed=999)
            save_config(custom, str(config_path))
            
            # Call ensure (should not overwrite)
            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                ensure_config_file()
                
                # Verify the custom value is preserved
                loaded = load_config()
                assert loaded.seed == 999
            finally:
                os.chdir(original_cwd)


class TestGetConfig:
    """Test get_config convenience function."""

    def test_get_config_returns_config(self):
        """Verify get_config returns a Config object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                config = get_config()
                assert isinstance(config, Config)
                assert config.seed == 42
                assert config.device == "cpu"
            finally:
                os.chdir(original_cwd)


import os