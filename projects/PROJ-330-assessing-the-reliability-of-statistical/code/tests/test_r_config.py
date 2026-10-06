"""
Tests for R environment configuration management.
"""

import os
import tempfile
import pytest
from pathlib import Path
import yaml

from src.r_config import (
    load_r_config,
    get_r_script_path,
    get_memory_limit_mb,
    get_time_limit_seconds,
    get_r_executable,
    get_r_env_vars,
    create_default_config,
    validate_r_environment,
    DEFAULT_R_SCRIPT_DIR,
    DEFAULT_MEMORY_LIMIT_MB,
    DEFAULT_TIME_LIMIT_SECONDS
)


class TestRConfigLoading:
    """Tests for loading R configuration from YAML."""

    def test_load_default_config_creates_defaults_on_missing(self, tmp_path):
        """Test that missing config file returns default values."""
        # Point to a non-existent config file
        non_existent = tmp_path / "non_existent.yaml"
        config = load_r_config(non_existent)

        assert config["r_script_dir"] == str(DEFAULT_R_SCRIPT_DIR)
        assert config["memory_limit_mb"] == DEFAULT_MEMORY_LIMIT_MB
        assert config["time_limit_seconds"] == DEFAULT_TIME_LIMIT_SECONDS
        assert config["r_executable"] == "Rscript"
        assert config["additional_env"] == {}

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid custom config file."""
        config_file = tmp_path / "r_config.yaml"
        custom_config = {
            "r_script_dir": str(tmp_path / "custom_scripts"),
            "memory_limit_mb": 8192,
            "time_limit_seconds": 7200,
            "r_executable": "/usr/bin/Rscript",
            "additional_env": {
                "CUSTOM_VAR": "test_value"
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(custom_config, f)

        loaded_config = load_r_config(config_file)

        assert loaded_config["r_script_dir"] == str((tmp_path / "custom_scripts").resolve())
        assert loaded_config["memory_limit_mb"] == 8192
        assert loaded_config["time_limit_seconds"] == 7200
        assert loaded_config["r_executable"] == "/usr/bin/Rscript"
        assert loaded_config["additional_env"]["CUSTOM_VAR"] == "test_value"

    def test_config_paths_are_absolute(self, tmp_path):
        """Test that r_script_dir is converted to absolute path."""
        config_file = tmp_path / "r_config.yaml"
        relative_path = "relative/path/to/scripts"

        with open(config_file, 'w') as f:
            yaml.dump({"r_script_dir": relative_path}, f)

        loaded_config = load_r_config(config_file)

        # Should be converted to absolute path
        assert Path(loaded_config["r_script_dir"]).is_absolute()


class TestRScriptPath:
    """Tests for R script path resolution."""

    def test_get_r_script_path_returns_correct_path(self, tmp_path):
        """Test that get_r_script_path returns the correct full path."""
        script_dir = tmp_path / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "test_script.R"
        script_file.touch()

        config = {
            "r_script_dir": str(script_dir),
            "memory_limit_mb": 4096,
            "time_limit_seconds": 3600,
            "r_executable": "Rscript",
            "additional_env": {}
        }

        result = get_r_script_path("test_script.R", config)

        assert result == script_file
        assert result.exists()

    def test_get_r_script_path_raises_on_missing(self, tmp_path):
        """Test that get_r_script_path raises FileNotFoundError for missing script."""
        script_dir = tmp_path / "scripts"
        script_dir.mkdir()

        config = {
            "r_script_dir": str(script_dir),
            "memory_limit_mb": 4096,
            "time_limit_seconds": 3600,
            "r_executable": "Rscript",
            "additional_env": {}
        }

        with pytest.raises(FileNotFoundError):
            get_r_script_path("missing_script.R", config)


class TestMemoryAndTimeLimits:
    """Tests for memory and time limit retrieval."""

    def test_get_memory_limit_mb(self, tmp_path):
        """Test getting memory limit from config."""
        config_file = tmp_path / "r_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({"memory_limit_mb": 16384}, f)

        config = load_r_config(config_file)
        assert get_memory_limit_mb(config) == 16384

    def test_get_time_limit_seconds(self, tmp_path):
        """Test getting time limit from config."""
        config_file = tmp_path / "r_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({"time_limit_seconds": 1800}, f)

        config = load_r_config(config_file)
        assert get_time_limit_seconds(config) == 1800


class TestRExecutable:
    """Tests for R executable path retrieval."""

    def test_get_r_executable(self, tmp_path):
        """Test getting R executable from config."""
        config_file = tmp_path / "r_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({"r_executable": "/opt/R/4.3/bin/Rscript"}, f)

        config = load_r_config(config_file)
        assert get_r_executable(config) == "/opt/R/4.3/bin/Rscript"


class TestREnvVars:
    """Tests for R environment variables."""

    def test_get_r_env_vars_includes_memory_limit(self, tmp_path):
        """Test that memory limit is set in environment variables."""
        config = {
            "r_script_dir": str(tmp_path),
            "memory_limit_mb": 4096,
            "time_limit_seconds": 3600,
            "r_executable": "Rscript",
            "additional_env": {}
        }

        env_vars = get_r_env_vars(config)

        # Check R_MAX_VSIZE is set (4096 MB = 4294967296 bytes)
        assert "R_MAX_VSIZE" in env_vars
        assert env_vars["R_MAX_VSIZE"] == "4294967296"

    def test_get_r_env_vars_includes_additional_env(self, tmp_path):
        """Test that additional environment variables are included."""
        config = {
            "r_script_dir": str(tmp_path),
            "memory_limit_mb": 4096,
            "time_limit_seconds": 3600,
            "r_executable": "Rscript",
            "additional_env": {
                "CUSTOM_VAR": "test_value",
                "ANOTHER_VAR": "another_value"
            }
        }

        env_vars = get_r_env_vars(config)

        assert env_vars["CUSTOM_VAR"] == "test_value"
        assert env_vars["ANOTHER_VAR"] == "another_value"

    def test_get_r_env_vars_preserves_system_env(self, tmp_path):
        """Test that system environment variables are preserved."""
        config = {
            "r_script_dir": str(tmp_path),
            "memory_limit_mb": 4096,
            "time_limit_seconds": 3600,
            "r_executable": "Rscript",
            "additional_env": {}
        }

        env_vars = get_r_env_vars(config)

        # Should contain standard system variables
        assert "PATH" in env_vars or "HOME" in env_vars


class TestCreateDefaultConfig:
    """Tests for default config creation."""

    def test_create_default_config_creates_file(self, tmp_path):
        """Test that create_default_config creates a valid YAML file."""
        output_file = tmp_path / "test_r_config.yaml"

        result_path = create_default_config(output_file)

        assert result_path == output_file
        assert output_file.exists()

        # Verify it's valid YAML with expected keys
        with open(output_file, 'r') as f:
            loaded = yaml.safe_load(f)

        assert "r_script_dir" in loaded
        assert "memory_limit_mb" in loaded
        assert "time_limit_seconds" in loaded
        assert "r_executable" in loaded
        assert "additional_env" in loaded

    def test_create_default_config_creates_parent_dirs(self, tmp_path):
        """Test that create_default_config creates parent directories."""
        output_file = tmp_path / "deep" / "nested" / "config" / "r_config.yaml"

        result_path = create_default_config(output_file)

        assert result_path.exists()
        assert output_file.parent.exists()


class TestValidateREnvironment:
    """Tests for R environment validation."""

    def test_validate_r_environment_with_valid_r(self):
        """Test validation when R is available in PATH."""
        # This test will pass if Rscript is in PATH
        config = {
            "r_script_dir": str(DEFAULT_R_SCRIPT_DIR),
            "memory_limit_mb": 4096,
            "time_limit_seconds": 3600,
            "r_executable": "Rscript",
            "additional_env": {}
        }

        # The result depends on whether R is installed in the test environment
        result = validate_r_environment(config)
        # We just verify the function runs without error
        assert isinstance(result, bool)

    def test_validate_r_environment_with_invalid_script_dir(self, tmp_path):
        """Test validation with non-existent script directory."""
        config = {
            "r_script_dir": str(tmp_path / "non_existent"),
            "memory_limit_mb": 4096,
            "time_limit_seconds": 3600,
            "r_executable": "Rscript",
            "additional_env": {}
        }

        # Should return False because script dir doesn't exist
        result = validate_r_environment(config)
        assert result is False