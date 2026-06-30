"""
Unit tests for environment configuration management.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config.env_config import (
    load_config, 
    setup_logging, 
    get_seed, 
    _get_env_int, 
    _get_env_float, 
    _get_env_str,
    DEFAULTS
)

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_content = """
    RANDOM_SEED=12345
    DATA_DIR=temp_data
    LOG_LEVEL=DEBUG
    BOOTSTRAP_COUNT=500
    TRAIN_TEST_SPLIT=0.8
    """
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file

def test_get_env_int_with_valid_value(monkeypatch):
    """Test retrieving an integer from environment."""
    monkeypatch.setenv("TEST_INT", "42")
    assert _get_env_int("TEST_INT", 10) == 42

def test_get_env_int_with_invalid_value(monkeypatch, caplog):
    """Test retrieving an integer with invalid input falls back to default."""
    monkeypatch.setenv("TEST_INT", "not_a_number")
    with caplog.at_level(logging.WARNING):
        result = _get_env_int("TEST_INT", 10)
    assert result == 10
    assert "Invalid integer" in caplog.text

def test_get_env_float_with_valid_value(monkeypatch):
    """Test retrieving a float from environment."""
    monkeypatch.setenv("TEST_FLOAT", "3.14")
    assert _get_env_float("TEST_FLOAT", 1.0) == pytest.approx(3.14)

def test_get_env_float_with_invalid_value(monkeypatch, caplog):
    """Test retrieving a float with invalid input falls back to default."""
    monkeypatch.setenv("TEST_FLOAT", "bad_float")
    with caplog.at_level(logging.WARNING):
        result = _get_env_float("TEST_FLOAT", 2.5)
    assert result == pytest.approx(2.5)
    assert "Invalid float" in caplog.text

def test_get_env_str(monkeypatch):
    """Test retrieving a string from environment."""
    monkeypatch.setenv("TEST_STR", "hello_world")
    assert _get_env_str("TEST_STR", "default") == "hello_world"

def test_load_config_creates_directories(tmp_path, monkeypatch):
    """Test that load_config creates necessary directories."""
    # Mock the project root
    monkeypatch.chdir(tmp_path)
    
    # Set specific env vars to avoid conflicts with real .env
    monkeypatch.setenv("DATA_DIR", "test_data_dir")
    monkeypatch.delenv("RANDOM_SEED", raising=False)
    
    config = load_config()
    
    assert config.data_dir.exists()
    assert config.results_dir.exists()
    assert config.derived_dir.exists()
    assert config.figures_dir.exists()

def test_load_config_defaults(monkeypatch):
    """Test that load_config uses defaults when env vars are missing."""
    # Clear relevant env vars
    for key in DEFAULTS.keys():
        monkeypatch.delenv(key, raising=False)
    
    config = load_config()
    
    assert config.random_seed == DEFAULTS["RANDOM_SEED"]
    assert config.bootstrap_count == int(DEFAULTS["BOOTSTRAP_COUNT"])
    assert config.train_test_split == float(DEFAULTS["TRAIN_TEST_SPLIT"])

def test_setup_logging_creates_file_handler(tmp_path, monkeypatch):
    """Test that setup_logging creates a file handler."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATA_DIR", "test_logs")
    
    config = load_config()
    logger = setup_logging(config)
    
    # Check that a file handler exists
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0

def test_get_seed(monkeypatch):
    """Test the convenience get_seed function."""
    monkeypatch.setenv("RANDOM_SEED", "999")
    seed = get_seed()
    assert seed == 999

def test_config_paths_are_absolute(tmp_path, monkeypatch):
    """Test that all config paths are absolute."""
    monkeypatch.chdir(tmp_path)
    config = load_config()
    
    assert config.data_dir.is_absolute()
    assert config.results_dir.is_absolute()
    assert config.derived_dir.is_absolute()
    assert config.figures_dir.is_absolute()
