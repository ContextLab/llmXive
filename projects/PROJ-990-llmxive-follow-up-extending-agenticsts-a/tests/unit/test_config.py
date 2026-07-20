import pytest
import os
from pathlib import Path
from code.config import load_config_from_file, ensure_directories, validate_config, DEFAULT_TOKEN_BUDGET

def test_load_default_config():
    """Test that default config loads correctly."""
    config = load_config_from_file()
    assert config["token_budget"] == DEFAULT_TOKEN_BUDGET
    assert config["min_context"] == 256
    assert "paths" in config

def test_validate_config_success():
    """Test validation with valid config."""
    config = load_config_from_file()
    # Ensure directories exist for validation
    ensure_directories(config)
    assert validate_config(config) is True

def test_validate_config_invalid_budget():
    """Test validation fails with low token budget."""
    config = load_config_from_file()
    config["token_budget"] = 512
    with pytest.raises(ValueError, match="TOKEN_BUDGET must be at least 1024"):
        validate_config(config)

def test_validate_config_invalid_split():
    """Test validation fails with invalid train split."""
    config = load_config_from_file()
    config["train_split"] = 1.5
    with pytest.raises(ValueError, match="TRAIN_SPLIT must be between 0 and 1"):
        validate_config(config)

def test_ensure_directories():
    """Test that ensure_directories creates the required folders."""
    config = load_config_from_file()
    # Remove a test dir to force creation
    test_dir = Path(config["paths"]["processed"])
    if test_dir.exists():
        test_dir.rmdir() # Only works if empty, but we assume fresh run for this test
    
    # Just ensure it doesn't crash
    ensure_directories(config)
    assert Path(config["paths"]["processed"]).exists()
