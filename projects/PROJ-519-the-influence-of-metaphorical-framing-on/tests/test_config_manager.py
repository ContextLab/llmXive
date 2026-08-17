"""
Tests for the configuration manager module.
"""
import os
import pytest
from pathlib import Path
from src.config_manager import (
    get_env_variable,
    get_data_path,
    get_config_path,
    is_debug_mode,
    use_real_data_only,
    ConfigError
)


def test_get_env_variable_with_existing_var(monkeypatch):
    """Test retrieving an existing environment variable."""
    monkeypatch.setenv("TEST_VAR", "test_value")
    assert get_env_variable("TEST_VAR") == "test_value"


def test_get_env_variable_with_default(monkeypatch):
    """Test retrieving a non-existing environment variable with a default."""
    if "NON_EXISTENT_VAR" in os.environ:
        del os.environ["NON_EXISTENT_VAR"]
    assert get_env_variable("NON_EXISTENT_VAR", "default_value") == "default_value"


def test_get_env_variable_required_missing(monkeypatch):
    """Test that a ConfigError is raised when a required variable is missing."""
    if "REQUIRED_VAR" in os.environ:
        del os.environ["REQUIRED_VAR"]
    with pytest.raises(ConfigError):
        get_env_variable("REQUIRED_VAR", required=True)


def test_get_data_path_default():
    """Test that get_data_path returns the default 'data' path."""
    # Ensure DATA_ROOT is not set to test default
    if "DATA_ROOT" in os.environ:
        del os.environ["DATA_ROOT"]
    path = get_data_path()
    assert path == Path("data")


def test_get_data_path_with_subdir(monkeypatch):
    """Test get_data_path with a subdirectory."""
    monkeypatch.setenv("DATA_ROOT", "custom_data")
    path = get_data_path("raw")
    assert path == Path("custom_data/raw")


def test_get_config_path_default():
    """Test that get_config_path returns the default 'config' path."""
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]
    path = get_config_path()
    assert path == Path("config")


def test_is_debug_mode_true(monkeypatch):
    """Test is_debug_mode returns True when DEBUG_MODE is 'true'."""
    monkeypatch.setenv("DEBUG_MODE", "true")
    assert is_debug_mode() is True


def test_is_debug_mode_false(monkeypatch):
    """Test is_debug_mode returns False when DEBUG_MODE is 'false'."""
    monkeypatch.setenv("DEBUG_MODE", "false")
    assert is_debug_mode() is False


def test_use_real_data_only_true(monkeypatch):
    """Test use_real_data_only returns True when USE_REAL_DATA_ONLY is 'true'."""
    monkeypatch.setenv("USE_REAL_DATA_ONLY", "true")
    assert use_real_data_only() is True


def test_use_real_data_only_false(monkeypatch):
    """Test use_real_data_only returns False when USE_REAL_DATA_ONLY is 'false'."""
    monkeypatch.setenv("USE_REAL_DATA_ONLY", "false")
    assert use_real_data_only() is False
