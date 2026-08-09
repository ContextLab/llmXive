"""Unit tests for configuration management (T004)."""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the module under test
from code.utils.config import Config, get_config, PROJECT_ROOT, DEFAULT_SEED

class TestConfig:
    """Tests for the Config class."""

    def test_default_initialization(self):
        """Test that Config loads with defaults when no file exists."""
        # Use a non-existent path to force defaults
        config = Config(config_path=Path("/nonexistent/path/config.yaml"))

        assert config.random_seed == DEFAULT_SEED
        assert config.max_exclusion_rate == 0.05
        assert config.cloud_threshold == 0.10
        assert config.data_dir == PROJECT_ROOT / "data"

    def test_file_initialization(self):
        """Test that Config loads from a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            test_data = {
                "hyperparams": {
                    "random_seed": 123,
                    "max_exclusion_rate": 0.10,
                    "cloud_threshold": 0.20
                },
                "paths": {
                    "data": "/custom/data/path"
                }
            }
            yaml.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            config = Config(config_path=temp_path)
            assert config.random_seed == 123
            assert config.max_exclusion_rate == 0.10
            assert config.cloud_threshold == 0.20
            assert config.data_dir == Path("/custom/data/path")
        finally:
            os.unlink(temp_path)

    def test_get_nested_value(self):
        """Test retrieving nested configuration values."""
        config = Config()
        assert config.get("hyperparams.random_seed") == DEFAULT_SEED
        assert config.get("paths.data") == str(PROJECT_ROOT / "data")
        assert config.get("nonexistent.key", "default") == "default"

    def test_ensure_directories(self):
        """Test that ensure_directories creates the folder structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a config pointing to a temp dir
            config_path = Path(tmpdir) / "config.yaml"
            test_config = {
                "paths": {
                    "data": str(Path(tmpdir) / "data"),
                    "raw": str(Path(tmpdir) / "data" / "raw"),
                    "processed": str(Path(tmpdir) / "data" / "processed"),
                    "final": str(Path(tmpdir) / "data" / "final"),
                    "code": str(Path(tmpdir) / "code"),
                    "tests": str(Path(tmpdir) / "tests"),
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)

            config = Config(config_path=config_path)
            config.ensure_directories()

            # Verify directories exist
            assert config.data_dir.exists()
            assert config.raw_dir.exists()
            assert config.processed_dir.exists()
            assert config.final_dir.exists()

    def test_singleton_pattern(self):
        """Test that get_config returns the same instance."""
        # Reset the singleton
        import code.utils.config as config_module
        config_module._config_instance = None

        c1 = get_config()
        c2 = get_config()

        assert c1 is c2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
