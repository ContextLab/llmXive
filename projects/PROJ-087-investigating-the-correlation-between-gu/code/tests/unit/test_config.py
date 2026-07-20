import os
import pytest
from src.config import load_config

def test_load_config_defaults(monkeypatch):
    """Test that load_config uses defaults when env vars are missing."""
    # Ensure DATA_URL is set for the test (required)
    monkeypatch.setenv("DATA_URL", "https://example.com/data.csv")
    # Unset optional vars to test defaults
    monkeypatch.delenv("RANDOM_SEED", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    config = load_config()

    assert config["DATA_URL"] == "https://example.com/data.csv"
    assert config["RANDOM_SEED"] == 42
    assert config["LOG_LEVEL"] == "INFO"

def test_load_config_custom_values(monkeypatch):
    """Test that load_config reads custom values from env vars."""
    monkeypatch.setenv("DATA_URL", "https://custom.example.com/data.csv")
    monkeypatch.setenv("RANDOM_SEED", "123")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    config = load_config()

    assert config["DATA_URL"] == "https://custom.example.com/data.csv"
    assert config["RANDOM_SEED"] == 123
    assert config["LOG_LEVEL"] == "DEBUG"

def test_load_config_missing_data_url(monkeypatch):
    """Test that load_config raises ValueError if DATA_URL is missing."""
    monkeypatch.delenv("DATA_URL", raising=False)
    monkeypatch.delenv("RANDOM_SEED", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    with pytest.raises(ValueError, match="Environment variable DATA_URL is not set"):
        load_config()

def test_load_config_invalid_random_seed(monkeypatch):
    """Test that load_config raises ValueError for invalid RANDOM_SEED."""
    monkeypatch.setenv("DATA_URL", "https://example.com/data.csv")
    monkeypatch.setenv("RANDOM_SEED", "not_an_integer")

    with pytest.raises(ValueError, match="RANDOM_SEED environment variable must be an integer"):
        load_config()

def test_load_config_invalid_log_level(monkeypatch):
    """Test that load_config raises ValueError for invalid LOG_LEVEL."""
    monkeypatch.setenv("DATA_URL", "https://example.com/data.csv")
    monkeypatch.setenv("LOG_LEVEL", "INVALID_LEVEL")

    with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
        load_config()