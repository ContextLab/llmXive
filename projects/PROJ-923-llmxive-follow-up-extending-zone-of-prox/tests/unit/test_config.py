"""
Unit tests for the configuration loader (T005).
Verifies that Config properties return correct types and default values,
and that reload_config raises appropriate errors.
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml

# Import the module under test
from config import Config, get_config, reload_config, CONFIG_PATH


class TestConfigClass:
    """Tests for the Config class properties."""

    def test_default_values(self):
        """Test that Config initializes with expected defaults when keys are missing."""
        data = {}
        cfg = Config(data)

        assert cfg.seed == 42
        assert cfg.buffer_cycles == 100
        assert cfg.noise_sigma == 0.05
        assert cfg.cap_rejected_threshold == 0.1
        assert cfg.cap_accepted_threshold == 0.9
        assert cfg.cap_min_candidates == 1
        assert cfg.log_level == 20  # INFO

    def test_custom_values(self):
        """Test that Config respects custom values provided in the dict."""
        data = {
            "project": {"seed": 123},
            "simulation": {"buffer_cycles": 50, "noise_sigma": 0.1},
            "caps": {"rejected_threshold": 0.05, "accepted_threshold": 0.95},
            "logging": {"level": "DEBUG"}
        }
        cfg = Config(data)

        assert cfg.seed == 123
        assert cfg.buffer_cycles == 50
        assert cfg.noise_sigma == 0.1
        assert cfg.cap_rejected_threshold == 0.05
        assert cfg.cap_accepted_threshold == 0.95
        assert cfg.log_level == 10  # DEBUG

    def test_paths_are_resolved(self):
        """Test that path properties return absolute Path objects."""
        data = {
            "paths": {
                "data_dir": "relative/path",
                "output_dir": "relative/output"
            }
        }
        cfg = Config(data)
        
        assert isinstance(cfg.data_dir, Path)
        assert cfg.data_dir.is_absolute()
        assert isinstance(cfg.output_dir, Path)
        assert cfg.output_dir.is_absolute()

class TestConfigLoader:
    """Tests for the config loading functions."""

    def test_reload_config_success(self, tmp_path):
        """Test successful reload from a valid config file."""
        # Create a temporary config file
        config_content = {
            "project": {"seed": 999},
            "simulation": {"buffer_cycles": 200}
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Temporarily override CONFIG_PATH
        original_path = CONFIG_PATH
        # Note: We can't easily override the global CONFIG_PATH in the module 
        # without patching, so we test the logic by creating the file at the 
        # expected location or mocking. 
        # For this unit test, we assume the global CONFIG_PATH is not used 
        # directly in the test environment, or we patch it.
        # A simpler approach for this specific test structure:
        
        # We will test the function logic by creating a file and ensuring 
        # the module can load it if we point CONFIG_PATH there.
        # Since CONFIG_PATH is a module-level constant, we need to patch it.
        
        import config as config_module
        
        # Save original
        original_config_path = config_module.CONFIG_PATH
        
        try:
            config_module.CONFIG_PATH = config_file
            # Clear the singleton to force reload
            config_module._config = None
            
            loaded_cfg = reload_config()
            
            assert loaded_cfg.seed == 999
            assert loaded_cfg.buffer_cycles == 200
        finally:
            # Restore
            config_module.CONFIG_PATH = original_config_path
            config_module._config = None

    def test_reload_config_missing_file(self, tmp_path):
        """Test that reload_config raises FileNotFoundError if file is missing."""
        import config as config_module
        
        fake_path = tmp_path / "nonexistent.yaml"
        original_path = config_module.CONFIG_PATH
        
        try:
            config_module.CONFIG_PATH = fake_path
            config_module._config = None
            
            with pytest.raises(FileNotFoundError, match="Configuration file not found"):
                reload_config()
        finally:
            config_module.CONFIG_PATH = original_path
            config_module._config = None

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        import config as config_module
        
        # Ensure clean state
        original_path = config_module.CONFIG_PATH
        config_module._config = None
        
        # Create a dummy config at the expected location to avoid error
        # This is a bit hacky for a unit test but ensures we don't need 
        # the actual project config.yaml to exist in the test environment.
        # We'll rely on the fact that if _config is None, it calls reload_config.
        # To avoid the FileNotFoundError, we patch CONFIG_PATH to a valid file.
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"project": {"seed": 1}}, f)
            temp_path = Path(f.name)
        
        try:
            config_module.CONFIG_PATH = temp_path
            
            cfg1 = get_config()
            cfg2 = get_config()
            
            assert cfg1 is cfg2
        finally:
            config_module.CONFIG_PATH = original_path
            config_module._config = None
            temp_path.unlink()