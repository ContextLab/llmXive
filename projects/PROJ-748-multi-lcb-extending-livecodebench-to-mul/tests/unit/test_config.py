"""
Unit tests for the configuration management module (code/config.py).
"""

import os
import tempfile
from pathlib import Path
import pytest

# Adjust import to match the project structure
# Assuming tests are run from the project root or PYTHONPATH is set correctly
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.config import (
    ProjectConfig, 
    get_config, 
    set_config, 
    get_data_path, 
    get_results_path, 
    get_models, 
    get_temperatures, 
    get_seed
)

class TestProjectConfig:
    def test_default_initialization(self):
        """Test that default values are set correctly."""
        cfg = ProjectConfig()
        assert isinstance(cfg.project_root, Path)
        assert cfg.random_seed == 42
        assert len(cfg.models) > 0
        assert 0.2 in cfg.temperatures
        assert 0.6 in cfg.temperatures
        assert 1.0 in cfg.temperatures
        assert cfg.timeout_seconds == 30

    def test_custom_initialization(self):
        """Test that custom values override defaults."""
        custom_models = ["model-A", "model-B"]
        custom_temps = [0.1, 0.9]
        custom_seed = 123
        
        cfg = ProjectConfig(
            random_seed=custom_seed,
            models=custom_models,
            temperatures=custom_temps
        )
        
        assert cfg.random_seed == custom_seed
        assert cfg.models == custom_models
        assert cfg.temperatures == custom_temps

    def test_path_resolution(self):
        """Test that paths are resolved relative to project root."""
        # Create a temporary directory to simulate a project root
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            cfg = ProjectConfig(project_root=tmp_path)
            
            expected_data = tmp_path / "data"
            expected_results = tmp_path / "results"
            
            assert cfg.data_dir == expected_data
            assert cfg.results_dir == expected_results

    def test_invalid_seed_type(self):
        """Test that invalid seed type raises error."""
        with pytest.raises(ValueError):
            ProjectConfig(random_seed="not_an_int")

    def test_invalid_model_type(self):
        """Test that invalid model type raises error."""
        with pytest.raises(ValueError):
            ProjectConfig(models=[123, "valid_model"])

    def test_invalid_temperature_type(self):
        """Test that invalid temperature type raises error."""
        with pytest.raises(ValueError):
            ProjectConfig(temperatures=[0.5, "high"])

class TestConfigAccessors:
    def setup_method(self):
        """Reset config before each test."""
        # Force a fresh config
        from code.config import _config
        # We need to access the private variable to reset it for testing
        # Since it's in the module, we can do:
        import code.config
        code.config._config = None

    def teardown_method(self):
        """Clean up after tests."""
        import code.config
        code.config._config = None

    def test_get_config_creates_default(self):
        """Test that get_config creates a default config if none exists."""
        cfg = get_config()
        assert cfg is not None
        assert cfg.random_seed == 42

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_set_config_overrides(self):
        """Test that set_config creates a new config with overrides."""
        new_seed = 999
        new_models = ["custom-model"]
        new_temps = [0.5]
        
        cfg = set_config(
            custom_seed=new_seed,
            custom_models=new_models,
            custom_temperatures=new_temps
        )
        
        assert cfg.random_seed == new_seed
        assert cfg.models == new_models
        assert cfg.temperatures == new_temps

        # Verify accessors reflect the new config
        assert get_seed() == new_seed
        assert get_models() == new_models
        assert get_temperatures() == new_temps

    def test_get_data_path(self):
        """Test get_data_path returns correct path."""
        cfg = set_config()
        assert get_data_path() == cfg.data_dir

    def test_get_results_path(self):
        """Test get_results_path returns correct path."""
        cfg = set_config()
        assert get_results_path() == cfg.results_dir

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
