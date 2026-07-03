"""
Unit tests for the configuration management module.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import Config, get_config, get_config_value, get_simulation_config, get_gnn_hyperparameters, get_paths

class TestConfig:
    """Test cases for Config class."""

    def test_default_config_creation(self):
        """Test that default config is created when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.yaml")
            config = Config(config_path)
            
            # Check default values exist
            assert config.get("seeds.random_seed") == 42
            assert config.get("paths.data_root") == "data"
            assert config.get("simulation.cores") == 2
            assert config.get("gnn.num_layers") == 2
            assert config.get("analysis.bond_cutoff") == 3.0

    def test_dot_notion_get(self):
        """Test getting values with dot notation."""
        config = Config()
        assert config.get("seeds.numpy_seed") == 42
        assert config.get("simulation.temperature") == 300.0
        assert config.get("analysis.exclusion_threshold") == 15.0

    def test_get_with_default(self):
        """Test getting value with default fallback."""
        config = Config()
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("seeds.random_seed", "default") == 42

    def test_set_value(self):
        """Test setting a value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.yaml")
            config = Config(config_path)
            
            config.set("custom.new_key", "new_value")
            assert config.get("custom.new_key") == "new_value"

    def test_save_config(self):
        """Test saving config to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "output.yaml")
            config = Config()
            config.set("test.key", "value")
            config.save(config_path)
            
            # Verify file exists and can be loaded
            assert os.path.exists(config_path)
            new_config = Config(config_path)
            assert new_config.get("test.key") == "value"

class TestGlobalFunctions:
    """Test global helper functions."""

    def test_get_config_singleton(self):
        """Test that get_config returns a singleton."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_value(self):
        """Test get_config_value convenience function."""
        val = get_config_value("seeds.random_seed")
        assert val == 42

    def test_get_simulation_config(self):
        """Test simulation config retrieval."""
        sim_config = get_simulation_config()
        assert "potential" in sim_config
        assert "timestep" in sim_config
        assert sim_config["cores"] == 2

    def test_get_gnn_hyperparameters(self):
        """Test GNN hyperparameter retrieval."""
        hparams = get_gnn_hyperparameters()
        assert hparams["num_layers"] == 2
        assert hparams["hidden_dim"] == 64
        assert hparams["learning_rate"] == 0.001

    def test_get_paths(self):
        """Test path retrieval."""
        paths = get_paths()
        assert "data_root" in paths
        assert "processed_graphs" in paths
        assert paths["data_root"] == "data"
