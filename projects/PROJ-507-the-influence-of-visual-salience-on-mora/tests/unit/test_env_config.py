"""
Unit tests for environment configuration management.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.env_config import (
    EnvConfig,
    EnvironmentConfigError,
    get_config,
    validate_environment,
    setup_env_file_example,
    _load_config_from_env
)


class TestEnvConfig:
    """Tests for the EnvConfig dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = EnvConfig()
        assert config.log_level == "INFO"
        assert config.seed == 42
        assert config.allow_synthetic is False
        assert config.visual_genome_path is None
        assert config.morald_path is None
        assert config.huggingface_token is None
        assert config.survey_api_key is None
        assert config.verified_data_source is None

    def test_custom_values(self):
        """Test that custom values are set correctly."""
        config = EnvConfig(
            visual_genome_path="/path/to/vg",
            morald_path="/path/to/morald",
            huggingface_token="test_token",
            log_level="DEBUG",
            seed=123,
            allow_synthetic=True
        )
        assert config.visual_genome_path == "/path/to/vg"
        assert config.morald_path == "/path/to/morald"
        assert config.huggingface_token == "test_token"
        assert config.log_level == "DEBUG"
        assert config.seed == 123
        assert config.allow_synthetic is True

    def test_derived_paths(self, tmp_path):
        """Test that derived paths are calculated correctly."""
        with patch.object(Path, '__new__', return_value=tmp_path):
            config = EnvConfig()
            # The project_root should be set correctly
            assert isinstance(config.project_root, Path)
            assert isinstance(config.data_raw_dir, Path)
            assert isinstance(config.data_processed_dir, Path)
            assert isinstance(config.data_survey_dir, Path)
            assert isinstance(config.data_synth_dir, Path)


class TestGetConfig:
    """Tests for the get_config function."""

    def test_singleton_pattern(self):
        """Test that get_config returns the same instance."""
        # Reset the singleton
        import code.env_config
        code.env_config._config_instance = None

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test_token_123"})
    def test_loads_from_environment(self):
        """Test that config is loaded from environment variables."""
        # Reset the singleton
        import code.env_config
        code.env_config._config_instance = None

        config = get_config()
        assert config.huggingface_token == "test_token_123"


class TestValidateEnvironment:
    """Tests for the validate_environment function."""

    def test_missing_required_variable(self):
        """Test that an error is raised when a required variable is missing."""
        # Ensure the variable is not set
        if "TEST_REQUIRED_VAR" in os.environ:
            del os.environ["TEST_REQUIRED_VAR"]

        with pytest.raises(EnvironmentConfigError) as exc_info:
            validate_environment(["TEST_REQUIRED_VAR"])

        assert "TEST_REQUIRED_VAR" in str(exc_info.value)

    @patch.dict(os.environ, {"TEST_VAR": "value"})
    def test_all_required_present(self):
        """Test that no error is raised when all required variables are present."""
        # Should not raise
        validate_environment(["TEST_VAR"])

    def test_multiple_missing_variables(self):
        """Test that all missing variables are reported."""
        # Ensure variables are not set
        for var in ["VAR1", "VAR2", "VAR3"]:
            if var in os.environ:
                del os.environ[var]

        with pytest.raises(EnvironmentConfigError) as exc_info:
            validate_environment(["VAR1", "VAR2", "VAR3"])

        assert "VAR1" in str(exc_info.value)
        assert "VAR2" in str(exc_info.value)
        assert "VAR3" in str(exc_info.value)


class TestSetupEnvFileExample:
    """Tests for the setup_env_file_example function."""

    def test_creates_file(self, tmp_path):
        """Test that the function creates an .env.example file."""
        output_path = str(tmp_path / ".env.example")
        result_path = setup_env_file_example(output_path)

        assert result_path == Path(output_path)
        assert Path(output_path).exists()

    def test_file_content(self, tmp_path):
        """Test that the file contains expected content."""
        output_path = str(tmp_path / ".env.example")
        setup_env_file_example(output_path)

        content = Path(output_path).read_text()
        assert "HUGGINGFACE_TOKEN" in content
        assert "VISUAL_GENOME_PATH" in content
        assert "MORALD_PATH" in content
        assert "SURVEY_API_KEY" in content
        assert "VERIFIED_DATA_SOURCE" in content
        assert "LOG_LEVEL" in content
        assert "RANDOM_SEED" in content
        assert "ALLOW_SYNTHETIC" in content

    def test_default_path(self, tmp_path, monkeypatch):
        """Test that the function uses the default path when not specified."""
        # Mock the parent path to point to tmp_path
        monkeypatch.setattr(Path, '__new__', lambda cls, *args, **kwargs: tmp_path)
        result_path = setup_env_file_example()
        assert result_path.name == ".env.example"


class TestLoadConfigFromEnv:
    """Tests for the _load_config_from_env function."""

    @patch.dict(os.environ, {
        "VISUAL_GENOME_PATH": "/vg/path",
        "MORALD_PATH": "/morald/path",
        "HUGGINGFACE_TOKEN": "hf_token",
        "SURVEY_API_KEY": "survey_key",
        "VERIFIED_DATA_SOURCE": "verified_source",
        "LOG_LEVEL": "DEBUG",
        "RANDOM_SEED": "999",
        "ALLOW_SYNTHETIC": "true"
    })
    def test_loads_all_variables(self):
        """Test that all environment variables are loaded correctly."""
        # Reset singleton to force reload
        import code.env_config
        code.env_config._config_instance = None

        config = _load_config_from_env()

        assert config.visual_genome_path == "/vg/path"
        assert config.morald_path == "/morald/path"
        assert config.huggingface_token == "hf_token"
        assert config.survey_api_key == "survey_key"
        assert config.verified_data_source == "verified_source"
        assert config.log_level == "DEBUG"
        assert config.seed == 999
        assert config.allow_synthetic is True

    def test_default_values_when_not_set(self):
        """Test that default values are used when environment variables are not set."""
        # Remove variables if they exist
        for var in [
            "VISUAL_GENOME_PATH", "MORALD_PATH", "HUGGINGFACE_TOKEN",
            "SURVEY_API_KEY", "VERIFIED_DATA_SOURCE", "LOG_LEVEL",
            "RANDOM_SEED", "ALLOW_SYNTHETIC"
        ]:
            if var in os.environ:
                del os.environ[var]

        # Reset singleton to force reload
        import code.env_config
        code.env_config._config_instance = None

        config = _load_config_from_env()

        assert config.visual_genome_path is None
        assert config.morald_path is None
        assert config.huggingface_token is None
        assert config.survey_api_key is None
        assert config.verified_data_source is None
        assert config.log_level == "INFO"  # default
        assert config.seed == 42  # default
        assert config.allow_synthetic is False  # default