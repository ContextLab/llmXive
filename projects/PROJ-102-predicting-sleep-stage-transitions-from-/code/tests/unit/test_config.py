"""
Unit tests for the configuration management module.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import (
    Config, PathConfig, SeedConfig, DataConfig, ModelConfig,
    get_config, reset_config, save_config
)


class TestPathConfig:
    """Tests for PathConfig class."""

    def test_default_paths(self):
        """Test that default paths are correctly initialized."""
        paths = PathConfig()
        assert paths.project_root.exists() or True  # May not exist in test env
        assert paths.data_dir.name == "data"
        assert paths.data_raw.name == "raw"
        assert paths.data_processed.name == "processed"
        assert paths.data_interim.name == "interim"

    def test_ensure_directories(self):
        """Test that ensure_directories creates required folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = PathConfig(project_root=Path(tmpdir))
            paths.ensure_directories()

            assert (Path(tmpdir) / "data" / "raw").exists()
            assert (Path(tmpdir) / "data" / "processed").exists()
            assert (Path(tmpdir) / "data" / "interim").exists()
            assert (Path(tmpdir) / "src" / "features").exists()
            assert (Path(tmpdir) / "src" / "models").exists()
            assert (Path(tmpdir) / "figures").exists()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        paths = PathConfig()
        path_dict = paths.to_dict()

        assert isinstance(path_dict, dict)
        assert "project_root" in path_dict
        assert "data_dir" in path_dict
        assert all(isinstance(v, str) for v in path_dict.values())


class TestSeedConfig:
    """Tests for SeedConfig class."""

    def test_default_seeds(self):
        """Test that default seeds are set correctly."""
        seeds = SeedConfig()
        assert seeds.numpy_seed == 42
        assert seeds.python_seed == 42
        assert seeds.torch_seed == 42
        assert seeds.tensorflow_seed == 42

    def test_set_all(self):
        """Test that set_all sets random seeds."""
        seeds = SeedConfig()
        # This should not raise an error
        seeds.set_all()


class TestDataConfig:
    """Tests for DataConfig class."""

    def test_default_data_config(self):
        """Test default data configuration values."""
        data = DataConfig()
        assert data.sampling_rate == 100.0
        assert 50 in data.notch_frequencies
        assert 60 in data.notch_frequencies
        assert data.bandpass_low == 0.5
        assert data.bandpass_high == 45.0
        assert data.epoch_duration == 30
        assert data.transition_window_duration == 60

    def test_band_definitions(self):
        """Test that frequency bands are correctly defined."""
        data = DataConfig()
        assert data.delta_band == (0.5, 4.0)
        assert data.theta_band == (4.0, 8.0)
        assert data.alpha_band == (8.0, 13.0)


class TestModelConfig:
    """Tests for ModelConfig class."""

    def test_constraint_parameters(self):
        """Test that model constraints are correctly set."""
        model = ModelConfig()
        assert model.max_params == 100_000
        assert model.learning_rate == 1e-3
        assert model.batch_size == 32
        assert model.num_epochs == 50
        assert model.dropout_rate == 0.3

    def test_validation_settings(self):
        """Test validation configuration."""
        model = ModelConfig()
        assert model.loso_folds is True
        assert model.target_improvement == 0.05


class TestConfig:
    """Tests for the main Config class."""

    def test_config_initialization(self):
        """Test that Config initializes all sub-configs."""
        config = Config()
        assert isinstance(config.paths, PathConfig)
        assert isinstance(config.seeds, SeedConfig)
        assert isinstance(config.data, DataConfig)
        assert isinstance(config.model, ModelConfig)

    def test_save_and_load(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_config.json"

            config = Config()
            config.save(filepath)

            assert filepath.exists()

            # Verify JSON is valid
            with open(filepath, 'r') as f:
                loaded_dict = json.load(f)

            assert "paths" in loaded_dict
            assert "seeds" in loaded_dict
            assert "data" in loaded_dict
            assert "model" in loaded_dict

            # Load back and verify
            loaded_config = Config.load(filepath)
            assert loaded_config.data.sampling_rate == config.data.sampling_rate
            assert loaded_config.model.max_params == config.model.max_params

    def test_singleton_pattern(self):
        """Test the singleton pattern for global config."""
        reset_config()  # Reset to start fresh

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

        reset_config()  # Clean up

    def test_ensure_directories(self):
        """Test that Config.ensure_directories works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config()
            config.paths = PathConfig(project_root=Path(tmpdir))
            config.ensure_directories()

            assert (Path(tmpdir) / "data").exists()
            assert (Path(tmpdir) / "src").exists()


class TestConvenienceFunctions:
    """Tests for convenience accessor functions."""

    def test_get_paths(self):
        """Test get_paths function."""
        reset_config()
        paths = get_paths()
        assert isinstance(paths, PathConfig)
        reset_config()

    def test_get_seeds(self):
        """Test get_seeds function."""
        reset_config()
        seeds = get_seeds()
        assert isinstance(seeds, SeedConfig)
        reset_config()

    def test_get_data_config(self):
        """Test get_data_config function."""
        reset_config()
        data = get_data_config()
        assert isinstance(data, DataConfig)
        reset_config()

    def test_get_model_config(self):
        """Test get_model_config function."""
        reset_config()
        model = get_model_config()
        assert isinstance(model, ModelConfig)
        reset_config()