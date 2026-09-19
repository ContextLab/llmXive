"""
Unit tests for configuration management.

Tests cover:
- Configuration loading from YAML
- Default values
- Path resolution
- Random seed setting
- Configuration validation
"""

import os
import tempfile
import pytest
from pathlib import Path
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import Config, get_config, set_random_seed, DEFAULT_CONFIG
from utils.config_loader import validate_config, load_config_from_env, merge_configs


class TestConfigInitialization:
    """Tests for Config class initialization."""

    def test_default_initialization(self):
        """Test that Config initializes with default values."""
        config = Config()
        
        assert config.random_seed == DEFAULT_CONFIG["seeds"]["random"]
        assert config.numpy_seed == DEFAULT_CONFIG["seeds"]["numpy"]
        assert config.max_memory_mb == DEFAULT_CONFIG["resources"]["max_memory_mb"]
        assert config.max_time_hours == DEFAULT_CONFIG["resources"]["max_time_hours"]
        assert config.min_samples == DEFAULT_CONFIG["analysis"]["min_samples"]
        assert config.alpha_fdr == DEFAULT_CONFIG["analysis"]["alpha_fdr"]

    def test_paths_are_absolute(self):
        """Test that all paths resolve to absolute paths."""
        config = Config()
        
        assert config.data_raw_path.is_absolute()
        assert config.data_processed_path.is_absolute()
        assert config.data_models_path.is_absolute()
        assert config.figures_path.is_absolute()
        assert config.logs_path.is_absolute()

    def test_directories_created(self):
        """Test that required directories are created on initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary config file to avoid side effects
            config_path = Path(tmpdir) / "test_config.py"
            config_path.write_text("DEFAULT_CONFIG = " + str(DEFAULT_CONFIG))
            
            config = Config()
            
            # Check that directories exist
            assert config.data_raw_path.parent.exists()
            assert config.data_processed_path.parent.exists()
            assert config.data_models_path.parent.exists()
            assert config.figures_path.parent.exists()
            assert config.logs_path.parent.exists()


class TestConfigLoading:
    """Tests for configuration loading from files."""

    def test_load_from_yaml(self, tmp_path):
        """Test loading configuration from a YAML file."""
        # Create a custom config file
        custom_config = {
            "paths": {"data_raw": "custom/raw"},
            "seeds": {"random": 123},
            "resources": {"max_memory_mb": 5000},
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(custom_config, f)
        
        # Temporarily change the project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            config = Config()
            assert config.data_raw_path.name == "custom"
            assert config.random_seed == 123
            assert config.max_memory_mb == 5000
        finally:
            os.chdir(original_cwd)

    def test_invalid_yaml_fallback(self, tmp_path):
        """Test that invalid YAML falls back to defaults."""
        # Create an invalid YAML file
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            config = Config()
            # Should fall back to defaults
            assert config.random_seed == DEFAULT_CONFIG["seeds"]["random"]
        finally:
            os.chdir(original_cwd)


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_valid_config(self):
        """Test validation of a valid configuration."""
        config = Config()
        warnings = validate_config(config)
        
        # Should have no warnings for valid config
        assert len(warnings) == 0

    def test_low_memory_warning(self):
        """Test warning for low memory limit."""
        config = Config()
        config._config["resources"]["max_memory_mb"] = 500
        
        warnings = validate_config(config)
        assert any("Memory limit too low" in w for w in warnings)

    def test_invalid_alpha_warning(self):
        """Test warning for invalid FDR alpha."""
        config = Config()
        config._config["analysis"]["alpha_fdr"] = 1.5
        
        warnings = validate_config(config)
        assert any("Invalid FDR alpha" in w for w in warnings)


class TestRandomSeeds:
    """Tests for random seed setting."""

    def test_set_random_seed(self):
        """Test that random seeds are set correctly."""
        import random
        import numpy as np
        
        # Set seeds
        set_random_seed()
        
        # Generate some values
        val1_random = random.random()
        val1_numpy = np.random.random()
        
        # Reset and generate again
        set_random_seed()
        val2_random = random.random()
        val2_numpy = np.random.random()
        
        # Should be identical
        assert val1_random == val2_random
        assert val1_numpy == val2_numpy


class TestConfigMerging:
    """Tests for configuration merging."""

    def test_merge_simple(self):
        """Test merging simple configuration dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        
        result = merge_configs(base, override)
        
        assert result["a"] == 1
        assert result["b"] == 3
        assert result["c"] == 4

    def test_merge_nested(self):
        """Test merging nested configuration dictionaries."""
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"c": 10, "e": 20}, "f": 30}
        
        result = merge_configs(base, override)
        
        assert result["a"]["b"] == 1
        assert result["a"]["c"] == 10
        assert result["a"]["e"] == 20
        assert result["d"] == 3
        assert result["f"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])