"""
Unit tests for the configuration loader.
"""

import os
import tempfile
import yaml
from pathlib import Path
import pytest

import sys
# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import Config, get_config, reload_config


class TestConfigInitialization:
    """Tests for Config class initialization."""

    def test_default_initialization(self, tmp_path):
        """Test that Config initializes with defaults when no file exists."""
        config = Config(project_root=tmp_path)
        assert config.global_seed == 42
        assert config.confidence_rejected == 0.1
        assert config.confidence_accepted == 0.9
        assert config.noise_std == 0.05
        assert config.num_buffer_cycles == 10

    def test_custom_config_file(self, tmp_path):
        """Test loading from a custom config file."""
        config_content = {
            "seeds": {"global_seed": 999},
            "thresholds": {"confidence_rejected": 0.2},
            "simulation": {"num_buffer_cycles": 20},
        }
        config_file = tmp_path / "custom_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = Config(config_path=config_file, project_root=tmp_path)
        assert config.global_seed == 999
        assert config.confidence_rejected == 0.2
        assert config.num_buffer_cycles == 20

    def test_nested_merge(self, tmp_path):
        """Test that nested config values are properly merged."""
        config_content = {
            "seeds": {"data_seed": 777},
            "thresholds": {"confidence_accepted": 0.95},
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = Config(config_path=config_file, project_root=tmp_path)
        # New values should be set
        assert config.data_seed == 777
        assert config.confidence_accepted == 0.95
        # Default values should remain
        assert config.global_seed == 42
        assert config.confidence_rejected == 0.1

    def test_path_resolution(self, tmp_path):
        """Test that relative paths are resolved to absolute paths."""
        config = Config(project_root=tmp_path)
        data_dir = Path(config._config["paths"]["data_dir"])
        assert data_dir.is_absolute()
        assert data_dir == tmp_path / "data"

    def test_project_root_in_config(self, tmp_path):
        """Test that project_root in config matches the provided root."""
        config = Config(project_root=tmp_path)
        assert Path(config._config["paths"]["project_root"]) == tmp_path


class TestConfigAccessors:
    """Tests for Config property accessors."""

    def test_seeds_property(self, tmp_path):
        """Test seeds property returns correct dict."""
        config = Config(project_root=tmp_path)
        seeds = config.seeds
        assert isinstance(seeds, dict)
        assert "global_seed" in seeds
        assert "data_seed" in seeds
        assert "model_seed" in seeds

    def test_thresholds_property(self, tmp_path):
        """Test thresholds property returns correct dict."""
        config = Config(project_root=tmp_path)
        thresholds = config.thresholds
        assert isinstance(thresholds, dict)
        assert "confidence_rejected" in thresholds
        assert "confidence_accepted" in thresholds
        assert "noise_std" in thresholds

    def test_simulation_property(self, tmp_path):
        """Test simulation property returns correct dict."""
        config = Config(project_root=tmp_path)
        sim = config.simulation
        assert isinstance(sim, dict)
        assert "num_buffer_cycles" in sim
        assert "num_tasks" in sim
        assert "num_seeds" in sim

    def test_mmlu_property(self, tmp_path):
        """Test mmlu property returns correct dict."""
        config = Config(project_root=tmp_path)
        mmlu = config.mmlu
        assert isinstance(mmlu, dict)
        assert "dataset_name" in mmlu
        assert "held_out_subjects" in mmlu

    def test_get_method(self, tmp_path):
        """Test the get method with dotted keys."""
        config = Config(project_root=tmp_path)
        assert config.get("seeds.global_seed") == 42
        assert config.get("thresholds.confidence_rejected") == 0.1
        assert config.get("simulation.num_buffer_cycles") == 10
        assert config.get("nonexistent.key", "default") == "default"


class TestConfigDirectories:
    """Tests for directory creation."""

    def test_ensure_directories(self, tmp_path):
        """Test that ensure_directories creates all required folders."""
        config = Config(project_root=tmp_path)
        config.ensure_directories()

        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "metrics").exists()
        assert (tmp_path / "figures").exists()
        assert (tmp_path / "data" / "logs").exists()
        assert (tmp_path / "contracts").exists()
        assert (tmp_path / "specs").exists()


class TestConfigSingleton:
    """Tests for the singleton pattern."""

    def test_get_config_returns_singleton(self, tmp_path):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reload_config_creates_new_instance(self, tmp_path):
        """Test that reload_config creates a new instance."""
        config1 = get_config()
        config2 = reload_config()
        assert config1 is not config2

    def test_get_config_with_path(self, tmp_path):
        """Test that get_config with a path creates a new instance."""
        config_content = {"seeds": {"global_seed": 111}}
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Clear singleton first
        from config import _config_instance
        import config
        config._config_instance = None

        config1 = get_config(config_path=config_file)
        assert config1.global_seed == 111

        # Get without path should return the same
        config2 = get_config()
        assert config2 is config1

        # Get with different path should create new
        config3 = get_config(config_path=tmp_path)
        assert config3 is not config2
        assert config3.global_seed == 42  # Default


class TestConfigSerialization:
    """Tests for config serialization."""

    def test_to_dict(self, tmp_path):
        """Test that to_dict returns a copy of the config."""
        config = Config(project_root=tmp_path)
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "seeds" in config_dict
        assert "thresholds" in config_dict
        assert config_dict is not config._config

    def test_repr(self, tmp_path):
        """Test that __repr__ returns a meaningful string."""
        config = Config(project_root=tmp_path)
        repr_str = repr(config)
        assert "Config" in repr_str
        assert str(tmp_path) in repr_str