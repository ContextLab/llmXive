"""
Unit tests for environment variable management (T008).
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from code.env_config import (
    EnvConfig,
    EnvironmentConfigError,
    get_config,
    validate_environment,
    setup_env_file_example,
)


class TestEnvConfig:
    """Tests for the EnvConfig class."""

    def test_missing_required_variable_raises_error(self):
        """Test that missing VISUAL_GENOME_PATH raises EnvironmentConfigError."""
        # Ensure the variable is not set
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            with pytest.raises(EnvironmentConfigError) as exc_info:
                _ = config.visual_genome_path

            assert "VISUAL_GENOME_PATH" in str(exc_info.value)
            assert "not set" in str(exc_info.value)

    def test_missing_required_variable_in_validate(self):
        """Test that validate_required() raises error for missing variables."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            with pytest.raises(EnvironmentConfigError) as exc_info:
                config.validate_required()

            assert "VISUAL_GENOME_PATH" in str(exc_info.value)

    def test_visual_genome_path_resolves_correctly(self):
        """Test that VISUAL_GENOME_PATH is correctly resolved."""
        test_path = "/tmp/test_visual_genome"
        with patch.dict(os.environ, {"VISUAL_GENOME_PATH": test_path}):
            config = EnvConfig()
            assert config.visual_genome_path == Path(test_path).resolve()

    def test_moral_d_path_optional(self):
        """Test that MORAL_D_PATH is optional and returns None if not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            assert config.moral_d_path is None

    def test_moral_d_path_set(self):
        """Test that MORAL_D_PATH is correctly resolved when set."""
        test_path = "/tmp/test_morald"
        with patch.dict(os.environ, {"MORAL_D_PATH": test_path}):
            config = EnvConfig()
            assert config.moral_d_path == Path(test_path).resolve()

    def test_huggingface_token_optional(self):
        """Test that HUGGINGFACE_TOKEN is optional."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            assert config.huggingface_token is None

    def test_huggingface_token_set(self):
        """Test that HUGGINGFACE_TOKEN is correctly retrieved."""
        test_token = "test_token_123"
        with patch.dict(os.environ, {"HUGGINGFACE_TOKEN": test_token}):
            config = EnvConfig()
            assert config.huggingface_token == test_token

    def test_clip_model_name_default(self):
        """Test that CLIP_MODEL_NAME defaults to 'ViT-B/32'."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            assert config.clip_model_name == "ViT-B/32"

    def test_clip_model_name_custom(self):
        """Test that CLIP_MODEL_NAME can be customized."""
        test_model = "ViT-L/14"
        with patch.dict(os.environ, {"CLIP_MODEL_NAME": test_model}):
            config = EnvConfig()
            assert config.clip_model_name == test_model

    def test_project_data_root_default(self):
        """Test that PROJECT_DATA_ROOT defaults to <project_root>/data."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig(base_path=Path("/test/project"))
            expected = Path("/test/project/data").resolve()
            assert config.project_data_root == expected

    def test_project_data_root_custom(self):
        """Test that PROJECT_DATA_ROOT can be customized."""
        test_path = "/custom/data/path"
        with patch.dict(os.environ, {"PROJECT_DATA_ROOT": test_path}):
            config = EnvConfig()
            assert config.project_data_root == Path(test_path).resolve()

    def test_verified_data_source(self):
        """Test that VERIFIED_DATA_SOURCE is correctly retrieved."""
        test_source = "visual_genome:train"
        with patch.dict(os.environ, {"VERIFIED_DATA_SOURCE": test_source}):
            config = EnvConfig()
            assert config.verified_data_source == test_source

    def test_get_all_config(self):
        """Test that get_all_config() returns a valid dictionary."""
        test_path = "/tmp/test_data"
        with patch.dict(
            os.environ,
            {
                "VISUAL_GENOME_PATH": test_path,
                "HUGGINGFACE_TOKEN": "test_token",
                "CLIP_MODEL_NAME": "ViT-L/14",
            },
        ):
            config = EnvConfig()
            all_config = config.get_all_config()

            assert isinstance(all_config, dict)
            assert "visual_genome_path" in all_config
            assert all_config["huggingface_token_set"] is True
            assert all_config["clip_model_name"] == "ViT-L/14"

    def test_cache_behavior(self):
        """Test that environment variables are cached after first access."""
        test_path = "/tmp/test_path"
        with patch.dict(os.environ, {"VISUAL_GENOME_PATH": test_path}):
            config = EnvConfig()
            # First access
            path1 = config.visual_genome_path
            # Modify env var (should not affect cached value)
            with patch.dict(os.environ, {"VISUAL_GENOME_PATH": "/tmp/new_path"}):
                path2 = config.visual_genome_path
            assert path1 == path2


class TestGlobalFunctions:
    """Tests for global helper functions."""

    def test_get_config_returns_singleton(self):
        """Test that get_config() returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_validate_environment_success(self):
        """Test that validate_environment() passes when all vars are set."""
        with patch.dict(os.environ, {"VISUAL_GENOME_PATH": "/tmp/test"}):
            # Should not raise
            validate_environment()

    def test_validate_environment_failure(self):
        """Test that validate_environment() fails when vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentConfigError):
                validate_environment()

    def test_setup_env_file_example(self, tmp_path):
        """Test that setup_env_file_example() creates a valid file."""
        output_path = tmp_path / ".env.example"
        result_path = setup_env_file_example(output_path)

        assert result_path == output_path
        assert output_path.exists()

        content = output_path.read_text()
        assert "VISUAL_GENOME_PATH" in content
        assert "MORAL_D_PATH" in content
        assert "HUGGINGFACE_TOKEN" in content