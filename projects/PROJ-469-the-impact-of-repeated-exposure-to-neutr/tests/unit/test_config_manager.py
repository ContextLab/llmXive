import os
import tempfile
from pathlib import Path
import pytest
import yaml

from config_manager import (
    load_env_file,
    load_config_file,
    merge_configs,
    get_config,
    get_path,
    get_data_raw_path,
    get_data_processed_path,
    get_results_path,
    get_logs_path,
    get_analysis_seed,
    get_alpha_level,
    get_bootstrap_count,
    create_sample_env_file,
    create_sample_config_file
)

class TestConfigManager:
    """Tests for environment configuration management."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up a temporary directory for each test."""
        self.tmp_path = tmp_path
        os.chdir(self.tmp_path)
        
        # Clear cache before each test
        import config_manager
        config_manager._config_cache.clear()
        config_manager._env_loaded = False
        
        yield

    def test_load_env_file_creates_dict(self):
        """Test that load_env_file returns a dictionary."""
        result = load_env_file()
        assert isinstance(result, dict)

    def test_load_config_file_raises_on_missing(self):
        """Test that load_config_file raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config_file("nonexistent.yaml")

    def test_merge_configs_overrides_yaml_with_env(self):
        """Test that environment variables override YAML config."""
        env_vars = {"DATA_RAW_PATH": "custom/raw"}
        yaml_config = {"paths": {"data_raw": "default/raw"}}
        
        merged = merge_configs(env_vars, yaml_config)
        assert merged["paths"]["data_raw"] == "custom/raw"

    def test_get_config_returns_merged_dict(self):
        """Test that get_config returns a dictionary."""
        # Create a sample config file
        config_path = self.tmp_path / "config.yaml"
        config_path.write_text("test_key: test_value")
        
        result = get_config()
        assert isinstance(result, dict)
        assert "test_key" in result

    def test_get_path_returns_path_object(self):
        """Test that get_path returns a Path object."""
        config_path = self.tmp_path / "config.yaml"
        config_path.write_text("paths:\n  data_raw: test/path")
        
        result = get_path("paths.data_raw")
        assert isinstance(result, Path)
        assert result == Path("test/path")

    def test_get_path_with_default(self):
        """Test that get_path returns default when key missing."""
        result = get_path("nonexistent.key", "default/path")
        assert result == Path("default/path")

    def test_get_data_raw_path(self):
        """Test get_data_raw_path returns correct path."""
        result = get_data_raw_path()
        assert isinstance(result, Path)

    def test_get_analysis_seed(self):
        """Test get_analysis_seed returns integer."""
        result = get_analysis_seed()
        assert isinstance(result, int)

    def test_get_alpha_level(self):
        """Test get_alpha_level returns float."""
        result = get_alpha_level()
        assert isinstance(result, float)
        assert 0.0 < result <= 1.0

    def test_get_bootstrap_count(self):
        """Test get_bootstrap_count returns integer."""
        result = get_bootstrap_count()
        assert isinstance(result, int)
        assert result > 0

    def test_create_sample_env_file(self):
        """Test that create_sample_env_file creates a valid .env file."""
        env_path = self.tmp_path / ".env"
        create_sample_env_file(str(env_path))
        
        assert env_path.exists()
        content = env_path.read_text()
        assert "DATA_RAW_PATH" in content
        assert "ANALYSIS_SEED" in content

    def test_create_sample_config_file(self):
        """Test that create_sample_config_file creates a valid YAML file."""
        config_path = self.tmp_path / "config.yaml"
        create_sample_config_file(str(config_path))
        
        assert config_path.exists()
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "paths" in config
        assert "defaults" in config
        assert config["paths"]["data_raw"] == "data/raw"

    def test_env_override_in_get_path(self):
        """Test that .env file overrides config.yaml for paths."""
        # Create config.yaml
        config_path = self.tmp_path / "config.yaml"
        config_path.write_text("paths:\n  data_raw: yaml/path")
        
        # Create .env
        env_path = self.tmp_path / ".env"
        env_path.write_text("DATA_RAW_PATH=env/path")
        
        # Clear cache
        import config_manager
        config_manager._config_cache.clear()
        config_manager._env_loaded = False
        
        result = get_data_raw_path()
        assert result == Path("env/path")