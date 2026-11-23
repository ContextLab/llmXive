"""
Unit tests for the configuration management module.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from src.config import Config, ConfigError, get_config

class TestConfigInitialization:
    """Tests for Config class initialization."""

    def test_load_default_config(self):
        """Test that default config is loaded when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.yaml")
            config = Config(config_path)
            
            assert config.distance_threshold == 2.0
            assert config.seed == 42
            assert config.get("simulation.distance_threshold_nm") == 2.0

    def test_load_custom_config(self):
        """Test loading a custom config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "custom.yaml")
            
            custom_config = {
                "simulation": {
                    "distance_threshold_nm": 3.5,
                    "statistical_override": True
                },
                "project": {
                    "seed": 123
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(custom_config, f)
            
            config = Config(config_path)
            
            assert config.distance_threshold == 3.5
            assert config.seed == 123
            assert config.get("simulation.statistical_override") is True

    def test_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises ConfigError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "invalid.yaml")
            
            with open(config_path, 'w') as f:
                f.write("invalid: yaml: content: [")
            
            with pytest.raises(ConfigError):
                Config(config_path)

class TestConfigAccess:
    """Tests for config value access methods."""

    def test_get_nested_value(self):
        """Test getting nested values with dot notation."""
        config = Config()
        
        assert config.get("simulation.distance_threshold_nm") == 2.0
        assert config.get("analysis.bootstrap_ci") == 0.95
        assert config.get("project.name") == "network-topology-heat-dissipation"

    def test_get_with_default(self):
        """Test getting values with default fallback."""
        config = Config()
        
        # Existing key
        assert config.get("simulation.distance_threshold_nm", 999) == 2.0
        
        # Non-existing key
        assert config.get("non.existent.key", "default") == "default"

    def test_set_value(self):
        """Test setting config values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = Config(config_path)
            
            config.set("simulation.distance_threshold_nm", 5.0)
            assert config.distance_threshold == 5.0
            
            config.set("new.nested.value", "test")
            assert config.get("new.nested.value") == "test"

    def test_save_config(self):
        """Test saving config to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "saved.yaml")
            config = Config(config_path)
            
            config.set("simulation.distance_threshold_nm", 4.0)
            config.save()
            
            # Reload and verify
            config2 = Config(config_path)
            assert config2.distance_threshold == 4.0

    def test_material_constants(self):
        """Test accessing material constants."""
        config = Config()
        
        assert config.get_material_constant("graphene", "lattice_constant_nm") == 0.246
        assert config.get_material_constant("graphene", "r_lattice") == 1000.0
        assert config.get_material_constant("mos2", "lattice_constant_nm") == 0.316
        
        # Non-existent material/constant
        assert config.get_material_constant("unknown", "lattice_constant_nm") is None
        assert config.get_material_constant("unknown", "lattice_constant_nm", 999) == 999

class TestGlobalConfig:
    """Tests for global config instance."""

    def test_global_config_singleton(self):
        """Test that get_config returns the same instance."""
        # Reset global config
        import src.config
        src.config._global_config = None
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2

    def test_global_config_path_override(self):
        """Test that global config respects path override."""
        import src.config
        src.config._global_config = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "global_test.yaml")
            custom_config = {"project": {"seed": 999}}
            with open(config_path, 'w') as f:
                yaml.dump(custom_config, f)
            
            config = get_config(config_path)
            assert config.seed == 999

class TestConfigProperties:
    """Tests for config property accessors."""

    def test_simulation_property(self):
        """Test simulation property returns dict."""
        config = Config()
        sim = config.simulation
        
        assert isinstance(sim, dict)
        assert "distance_threshold_nm" in sim

    def test_analysis_property(self):
        """Test analysis property returns dict."""
        config = Config()
        analysis = config.analysis
        
        assert isinstance(analysis, dict)
        assert "bootstrap_ci" in analysis

    def test_data_property(self):
        """Test data property returns dict."""
        config = Config()
        data = config.data
        
        assert isinstance(data, dict)
        assert "raw_dir" in data

    def test_logging_property(self):
        """Test logging property returns dict."""
        config = Config()
        logging = config.logging
        
        assert isinstance(logging, dict)
        assert "level" in logging