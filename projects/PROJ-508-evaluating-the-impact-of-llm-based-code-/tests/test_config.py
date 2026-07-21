"""
Tests for the configuration module (code/utils/config.py).
"""
import os
from pathlib import Path

import pytest

from utils.config import Config, get_config


def test_config_defaults(monkeypatch):
    """Test that Config uses sensible defaults when env vars are missing."""
    # Ensure no specific env vars are set
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("DATA_DIR", raising=False)

    config = Config()

    assert config.github_token is None
    assert isinstance(config.data_dir, Path)
    assert config.data_dir.name == "data"


def test_config_from_env(monkeypatch):
    """Test that Config reads from environment variables."""
    test_token = "ghp_test123"
    test_data_dir = "/tmp/test_data"

    monkeypatch.setenv("GITHUB_TOKEN", test_token)
    monkeypatch.setenv("DATA_DIR", test_data_dir)

    config = Config()

    assert config.github_token == test_token
    assert str(config.data_dir) == test_data_dir


def test_get_config_singleton(monkeypatch):
    """Test that get_config returns a consistent instance."""
    monkeypatch.setenv("TEST_VAR", "value1")
    cfg1 = get_config()

    monkeypatch.setenv("TEST_VAR", "value2")
    cfg2 = get_config()

    # The singleton should be the same instance
    assert cfg1 is cfg2
