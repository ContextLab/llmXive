"""
Unit tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.config import Config, get_config, load_config, PROJECT_ROOT


class TestConfig:
    """Test cases for the Config class."""

    def test_default_initialization(self):
        """Test that config initializes with defaults when no .env exists."""
        # Create a temporary directory to avoid interfering with project .env
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            env_file = tmp_path / ".env"
            
            # Don't create .env file
            config = Config(env_file)
            
            # Check defaults are set
            assert config.data_source == "synthetic"
            assert config.random_seed == 42
            assert config.log_level == "INFO"
            assert config.max_workers == 4

    def test_env_file_loading(self):
        """Test that config loads values from .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            env_file = tmp_path / ".env"
            
            # Write custom values
            with open(env_file, 'w') as f:
                f.write("NPY_RNG_SEED=123\n")
                f.write("DATA_SOURCE=real\n")
                f.write("LOG_LEVEL=DEBUG\n")
                f.write("MAX_WORKERS=8\n")
            
            config = Config(env_file)
            
            assert config.random_seed == 123
            assert config.data_source == "real"
            assert config.log_level == "DEBUG"
            assert config.max_workers == 8

    def test_type_casting(self):
        """Test that config correctly casts values to different types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            env_file = tmp_path / ".env"
            
            with open(env_file, 'w') as f:
                f.write("NPY_RNG_SEED=42\n")
                f.write("MAX_WORKERS=4\n")
                f.write("TIMEOUT_SECONDS=7200\n")
                f.write("DATA_SOURCE=true\n")
            
            config = Config(env_file)
            
            # Test integer casting
            assert config.get_int("NPY_RNG_SEED") == 42
            assert config.get_int("MAX_WORKERS") == 4
            
            # Test float casting
            assert config.get_float("TIMEOUT_SECONDS") == 7200.0
            
            # Test boolean casting
            assert config.get_bool("DATA_SOURCE") is True

    def test_path_conversion(self):
        """Test that config correctly converts paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            env_file = tmp_path / ".env"
            
            test_path = tmp_path / "custom" / "data"
            with open(env_file, 'w') as f:
                f.write(f"DATA_PATH={test_path}\n")
            
            config = Config(env_file)
            
            result_path = config.get_path("DATA_PATH")
            assert isinstance(result_path, Path)
            assert result_path == test_path

    def test_ensure_paths_exist(self):
        """Test that ensure_paths_exist creates directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            env_file = tmp_path / ".env"
            
            # Create paths that don't exist
            data_path = tmp_path / "data" / "raw"
            output_path = tmp_path / "data" / "results"
            
            with open(env_file, 'w') as f:
                f.write(f"DATA_PATH={data_path}\n")
                f.write(f"OUTPUT_PATH={output_path}\n")
                f.write(f"FIGURE_PATH={tmp_path / 'figures'}\n")
                f.write(f"CACHE_PATH={tmp_path / 'cache'}\n")
            
            config = Config(env_file)
            config.ensure_paths_exist()
            
            # Verify directories were created
            assert data_path.exists()
            assert output_path.exists()
            assert (tmp_path / "figures").exists()
            assert (tmp_path / "cache").exists()

    def test_to_dict_and_json(self):
        """Test that config can be serialized to dict and JSON."""
        config = Config()
        
        # Test dict conversion
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "DATA_SOURCE" in config_dict
        assert "NPY_RNG_SEED" in config_dict
        
        # Test JSON conversion
        json_str = config.to_json()
        assert isinstance(json_str, str)
        assert "DATA_SOURCE" in json_str

    def test_global_config_instance(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_load_config_function(self):
        """Test that load_config creates a new Config instance."""
        config = load_config()
        assert isinstance(config, Config)

    def test_missing_required_vars_handling(self):
        """Test that missing required vars are set to defaults."""
        # Remove required vars from environment if they exist
        original_env = {}
        for key in ["PYTHONHASHSEED", "NPY_RNG_SEED", "LOG_LEVEL"]:
            if key in os.environ:
                original_env[key] = os.environ[key]
                del os.environ[key]
        
        try:
            config = Config()
            
            # Check that defaults were set in environment
            assert os.environ.get("PYTHONHASHSEED") == "42"
            assert os.environ.get("NPY_RNG_SEED") == "42"
            assert os.environ.get("LOG_LEVEL") == "INFO"
            
            # Check config values
            assert config.random_seed == 42
            assert config.log_level == "INFO"
        finally:
            # Restore original environment
            for key, value in original_env.items():
                os.environ[key] = value

    def test_property_accessors(self):
        """Test that property accessors return correct types."""
        config = Config()
        
        assert isinstance(config.data_source, str)
        assert isinstance(config.data_path, Path)
        assert isinstance(config.output_path, Path)
        assert isinstance(config.figure_path, Path)
        assert isinstance(config.cache_path, Path)
        assert isinstance(config.log_level, str)
        assert isinstance(config.random_seed, int)
        assert isinstance(config.max_workers, int)
        assert isinstance(config.timeout_seconds, int)
        assert isinstance(config.to_dict(), dict)