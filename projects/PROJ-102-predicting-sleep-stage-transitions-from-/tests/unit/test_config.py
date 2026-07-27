"""
Unit tests for configuration management.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.config import (
    PathConfig,
    SeedConfig,
    DataConfig,
    ModelConfig,
    Config,
    get_config,
    reset_config,
    save_config,
    get_paths,
    get_seeds,
    get_data_config,
    get_model_config
)


class TestPathConfig:
    """Tests for PathConfig class."""

    def test_default_paths(self):
        """Test that default paths are correctly initialized."""
        config = PathConfig()
        assert config.root is not None
        assert config.data_raw == config.root / "data" / "raw"
        assert config.data_processed == config.root / "data" / "processed"
        assert config.data_interim == config.root / "data" / "interim"
        assert config.src == config.root / "src"
        assert config.tests == config.root / "tests"
        assert config.specs == config.root / "specs"
        assert config.figures == config.root / "figures"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = PathConfig()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'root' in config_dict
        assert 'data_raw' in config_dict
        assert isinstance(config_dict['root'], str)
        assert isinstance(config_dict['data_raw'], str)

    def test_custom_root(self):
        """Test initialization with custom root path."""
        custom_root = Path("/custom/project/root")
        config = PathConfig(root=custom_root)
        assert config.root == custom_root
        assert config.data_raw == custom_root / "data" / "raw"


class TestSeedConfig:
    """Tests for SeedConfig class."""

    def test_default_seeds(self):
        """Test default seed values."""
        config = SeedConfig()
        assert config.numpy == 42
        assert config.python == 42
        assert config.torch is None
        assert config.tensorflow is None

    def test_custom_seeds(self):
        """Test custom seed values."""
        config = SeedConfig(numpy=123, python=456, torch=789)
        assert config.numpy == 123
        assert config.python == 456
        assert config.torch == 789


class TestDataConfig:
    """Tests for DataConfig class."""

    def test_default_data_config(self):
        """Test default data configuration values."""
        config = DataConfig()
        assert config.sampling_rate == 100.0
        assert config.bandpass_low == 0.5
        assert config.bandpass_high == 45.0
        assert config.epoch_duration == 30
        assert config.transition_window_duration == 60
        assert config.batch_size == 32
        assert config.shuffle is True

    def test_custom_data_config(self):
        """Test custom data configuration values."""
        config = DataConfig(
            sampling_rate=200.0,
            epoch_duration=60,
            batch_size=64,
            shuffle=False
        )
        assert config.sampling_rate == 200.0
        assert config.epoch_duration == 60
        assert config.batch_size == 64
        assert config.shuffle is False


class TestModelConfig:
    """Tests for ModelConfig class."""

    def test_default_model_config(self):
        """Test default model configuration values."""
        config = ModelConfig()
        assert config.max_parameters == 100000
        assert config.learning_rate == 1e-3
        assert config.epochs == 50
        assert config.dropout_rate == 0.5
        assert config.cv_folds == 5
        assert config.leave_one_subject_out is True

    def test_custom_model_config(self):
        """Test custom model configuration values."""
        config = ModelConfig(
            max_parameters=50000,
            learning_rate=1e-4,
            epochs=100
        )
        assert config.max_parameters == 50000
        assert config.learning_rate == 1e-4
        assert config.epochs == 100


class TestConfig:
    """Tests for master Config class."""

    def test_default_config(self):
        """Test that default config initializes all components."""
        config = Config()
        assert isinstance(config.paths, PathConfig)
        assert isinstance(config.seeds, SeedConfig)
        assert isinstance(config.data, DataConfig)
        assert isinstance(config.model, ModelConfig)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        assert 'paths' in config_dict
        assert 'seeds' in config_dict
        assert 'data' in config_dict
        assert 'model' in config_dict

    def test_save_and_load(self):
        """Test saving and loading configuration."""
        config = Config()
        config.data.epoch_duration = 60
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_config.json"
            config.save(filepath)
            
            # Verify file was created
            assert filepath.exists()
            
            # Load and verify
            loaded_config = Config.load(filepath)
            assert loaded_config.data.epoch_duration == 60
            assert loaded_config.paths == config.paths

    def test_save_default_location(self):
        """Test saving to default location."""
        config = Config()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override root path
            original_root = config.paths.root
            config.paths.root = Path(tmpdir)
            
            config.save()
            
            # Restore original root
            config.paths.root = original_root
            
            # Check file was created
            default_path = Path(tmpdir) / "config.json"
            assert default_path.exists()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_config(self):
        """Test getting global config."""
        reset_config()  # Ensure fresh state
        config = get_config()
        assert isinstance(config, Config)

    def test_get_paths(self):
        """Test getting path config."""
        reset_config()
        paths = get_paths()
        assert isinstance(paths, PathConfig)

    def test_get_seeds(self):
        """Test getting seed config."""
        reset_config()
        seeds = get_seeds()
        assert isinstance(seeds, SeedConfig)

    def test_get_data_config(self):
        """Test getting data config."""
        reset_config()
        data_config = get_data_config()
        assert isinstance(data_config, DataConfig)

    def test_get_model_config(self):
        """Test getting model config."""
        reset_config()
        model_config = get_model_config()
        assert isinstance(model_config, ModelConfig)

    def test_reset_config(self):
        """Test resetting global config."""
        reset_config()
        original_config = get_config()
        original_epochs = original_config.model.epochs
        
        # Modify config
        get_config().model.epochs = 999
        
        # Reset
        reset_config()
        new_config = get_config()
        
        assert new_config.model.epochs != 999
        assert new_config.model.epochs == original_epochs

    def test_save_config(self):
        """Test saving global config."""
        reset_config()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "global_config.json"
            save_config(filepath)
            
            assert filepath.exists()
            
            # Verify content
            with open(filepath, 'r') as f:
                data = json.load(f)
            assert 'paths' in data
            assert 'seeds' in data