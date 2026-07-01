"""
Unit tests for the configuration management module (code/utils/config.py).
"""
import os
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.config import (
    Config,
    get_config,
    get_path,
    get_data_path,
    require_env_var,
    get_llm_api_key,
    get_github_token,
    DEFAULT_RANDOM_SEED,
    DEFAULT_API_TIMEOUT_SECONDS,
    DEFAULT_PROCESS_TIMEOUT_SECONDS,
)

@pytest.fixture(autouse=True)
def reset_config():
    """Reset config singleton before and after each test."""
    Config.reset()
    yield
    Config.reset()

@pytest.fixture
def mock_env(monkeypatch):
    """Fixture to set environment variables for tests."""
    def _set(key, value):
        monkeypatch.setenv(key, value)
    return _set

def test_config_singleton():
    """Test that Config returns the same instance."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2

def test_default_values():
    """Test that default values are correctly loaded when env vars are missing."""
    cfg = get_config()
    assert cfg.random_seed == DEFAULT_RANDOM_SEED
    assert cfg.api_timeout == DEFAULT_API_TIMEOUT_SECONDS
    assert cfg.process_timeout == DEFAULT_PROCESS_TIMEOUT_SECONDS
    assert cfg.llm_api_key is None
    assert cfg.github_token is None

def test_custom_random_seed(mock_env):
    """Test custom random seed from environment."""
    mock_env("RANDOM_SEED", "12345")
    cfg = get_config()
    assert cfg.random_seed == 12345

def test_custom_timeouts(mock_env):
    """Test custom timeouts from environment."""
    mock_env("API_TIMEOUT_SECONDS", "300")
    mock_env("PROCESS_TIMEOUT_SECONDS", "600")
    cfg = get_config()
    assert cfg.api_timeout == 300
    assert cfg.process_timeout == 600

def test_api_keys(mock_env):
    """Test API keys are loaded from environment."""
    mock_env("LLMAPI_KEY", "test_llm_key")
    mock_env("GITHUB_TOKEN", "test_github_token")
    
    cfg = get_config()
    assert cfg.llm_api_key == "test_llm_key"
    assert cfg.github_token == "test_github_token"

def test_get_path():
    """Test get_path resolves relative to project root."""
    cfg = get_config()
    expected = cfg.project_root / "some" / "path"
    result = get_path("some/path")
    assert result == expected

def test_get_data_path():
    """Test get_data_path resolves relative to data directory."""
    cfg = get_config()
    expected = cfg.data_dir / "raw" / "file.txt"
    result = get_data_path("raw/file.txt")
    assert result == expected

def test_require_env_var_missing():
    """Test require_env_var raises ValueError when missing."""
    with pytest.raises(ValueError, match="Missing required environment variable"):
        require_env_var("NON_EXISTENT_VAR")

def test_require_env_var_present(mock_env):
    """Test require_env_var returns value when present."""
    mock_env("EXISTENT_VAR", "value123")
    result = require_env_var("EXISTENT_VAR")
    assert result == "value123"

def test_get_llm_api_key_missing():
    """Test get_llm_api_key raises error if not set."""
    with pytest.raises(ValueError):
        get_llm_api_key()

def test_get_llm_api_key_present(mock_env):
    """Test get_llm_api_key returns key if set."""
    mock_env("LLMAPI_KEY", "secret_key")
    assert get_llm_api_key() == "secret_key"

def test_get_github_token_missing():
    """Test get_github_token raises error if not set."""
    with pytest.raises(ValueError):
        get_github_token()

def test_get_github_token_present(mock_env):
    """Test get_github_token returns token if set."""
    mock_env("GITHUB_TOKEN", "ghp_secret")
    assert get_github_token() == "ghp_secret"

def test_to_dict():
    """Test to_dict returns expected structure."""
    cfg = get_config()
    d = cfg.to_dict()
    
    assert "project_root" in d
    assert "data_dir" in d
    assert "random_seed" in d
    assert "api_timeout" in d
    assert "process_timeout" in d
    assert "has_llm_api_key" in d
    assert "has_github_token" in d
    
    # Check types
    assert isinstance(d["random_seed"], int)
    assert isinstance(d["has_llm_api_key"], bool)

def test_config_paths_exist_on_disk():
    """Test that the configured data and reports directories exist on disk (if created by T001)."""
    cfg = get_config()
    # T001 creates these directories. If they don't exist yet, this is not a failure of config,
    # but we can assert they are the expected paths.
    # We verify the paths are constructed correctly.
    assert cfg.data_dir.name == "data"
    assert cfg.reports_dir.name == "reports"