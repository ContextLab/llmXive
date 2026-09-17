"""
Tests for environment variable management.
"""
import os
import pytest
from unittest.mock import patch
from pathlib import Path

# Import from the module we are testing
from code.config.env_manager import (
    get_required_env,
    validate_hf_token,
    get_hf_paths,
    setup_environment,
    EnvironmentError,
    HF_TOKEN_VAR,
    DEFAULT_HF_HOME
)


class TestGetRequiredEnv:
    def test_returns_value_when_set(self):
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_required_env("TEST_VAR", "Test Description")
            assert result == "test_value"

    def test_raises_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError) as exc_info:
                get_required_env("MISSING_VAR", "Missing Description")
            assert "Missing required environment variable 'MISSING_VAR'" in str(exc_info.value)

    def test_raises_when_empty(self):
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            with pytest.raises(EnvironmentError) as exc_info:
                get_required_env("EMPTY_VAR", "Empty Description")
            assert "Missing required environment variable 'EMPTY_VAR'" in str(exc_info.value)


class TestValidateHfToken:
    def test_returns_token_when_valid(self):
        fake_token = "hf_test123456789"
        with patch.dict(os.environ, {HF_TOKEN_VAR: fake_token}):
            result = validate_hf_token()
            assert result == fake_token

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError):
                validate_hf_token()


class TestGetHfPaths:
    def test_uses_default_if_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            hf_home, cache = get_hf_paths()
            assert hf_home == DEFAULT_HF_HOME
            assert cache is None

    def test_uses_custom_hf_home(self):
        custom_home = "/custom/hf/home"
        with patch.dict(os.environ, {"HF_HOME": custom_home}):
            hf_home, cache = get_hf_paths()
            assert str(hf_home) == custom_home

    def test_uses_custom_cache(self):
        custom_cache = "/custom/cache"
        with patch.dict(os.environ, {"HF_DATASETS_CACHE": custom_cache}):
            hf_home, cache = get_hf_paths()
            assert str(cache) == custom_cache

    def test_uses_both_custom(self):
        custom_home = "/custom/hf"
        custom_cache = "/custom/cache"
        with patch.dict(os.environ, {
            "HF_HOME": custom_home,
            "HF_DATASETS_CACHE": custom_cache
        }):
            hf_home, cache = get_hf_paths()
            assert str(hf_home) == custom_home
            assert str(cache) == custom_cache


class TestSetupEnvironment:
    def test_successful_setup(self):
        fake_token = "hf_valid_token"
        with patch.dict(os.environ, {HF_TOKEN_VAR: fake_token}):
            config = setup_environment()
            assert config["token"] == fake_token
            assert "hf_home" in config
            assert "datasets_cache" in config

    def test_raises_on_missing_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError):
                setup_environment()

    def test_creates_directories_if_custom(self, tmp_path):
        custom_home = str(tmp_path / "hf")
        custom_cache = str(tmp_path / "cache")
        
        with patch.dict(os.environ, {
            HF_TOKEN_VAR: "hf_token",
            "HF_HOME": custom_home,
            "HF_DATASETS_CACHE": custom_cache
        }):
            # Initially directories don't exist
            assert not os.path.exists(custom_home)
            
            config = setup_environment()
            
            # Now they should exist
            assert os.path.exists(custom_home)
            assert os.path.exists(custom_cache)
            assert config["hf_home"] == custom_home
            assert config["datasets_cache"] == custom_cache
