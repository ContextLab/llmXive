import os
import json
import tempfile
from pathlib import Path
import pytest
from code.config.settings import (
    APIKeys, DatasetPaths, Config, 
    load_config_from_env, load_config_from_file, get_config
)

def test_api_keys_default_values():
    """Test that APIKeys has correct default values."""
    keys = APIKeys()
    assert keys.pushshift_api_key is None
    assert keys.reddit_client_id is None
    assert keys.reddit_client_secret is None
    assert keys.reddit_user_agent == "llmXive-emotional-contagion:1.0"

def test_api_keys_with_values():
    """Test APIKeys with provided values."""
    keys = APIKeys(
        pushshift_api_key="test_key",
        reddit_client_id="test_id",
        reddit_client_secret="test_secret",
        reddit_user_agent="custom_agent"
    )
    assert keys.pushshift_api_key == "test_key"
    assert keys.reddit_client_id == "test_id"
    assert keys.reddit_client_secret == "test_secret"
    assert keys.reddit_user_agent == "custom_agent"

def test_dataset_paths_default_values():
    """Test that DatasetPaths has correct default values."""
    paths = DatasetPaths()
    assert paths.raw_dir == Path("data/raw")
    assert paths.processed_dir == Path("data/processed")
    assert paths.annotations_file == Path("data/raw/annotations.json")

def test_dataset_paths_creates_directories():
    """Test that DatasetPaths creates directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "new_raw"
        processed_dir = Path(tmpdir) / "new_processed"
        
        paths = DatasetPaths(raw_dir=raw_dir, processed_dir=processed_dir)
        
        assert raw_dir.exists()
        assert processed_dir.exists()

def test_config_default_values():
    """Test that Config has correct default values."""
    config = Config()
    assert isinstance(config.api_keys, APIKeys)
    assert isinstance(config.dataset_paths, DatasetPaths)
    assert config.debug_mode is False
    assert config.random_seed == 42
    assert config.max_threads == 500
    assert config.min_replies_for_contagion == 5

def test_load_config_from_env():
    """Test loading config from environment variables."""
    os.environ["PUSHSHIFT_API_KEY"] = "env_key"
    os.environ["REDDIT_CLIENT_ID"] = "env_id"
    os.environ["REDDIT_CLIENT_SECRET"] = "env_secret"
    os.environ["DEBUG_MODE"] = "true"
    os.environ["RANDOM_SEED"] = "123"
    
    config = load_config_from_env()
    
    assert config.api_keys.pushshift_api_key == "env_key"
    assert config.api_keys.reddit_client_id == "env_id"
    assert config.api_keys.reddit_client_secret == "env_secret"
    assert config.debug_mode is True
    assert config.random_seed == 123
    
    # Clean up
    del os.environ["PUSHSHIFT_API_KEY"]
    del os.environ["REDDIT_CLIENT_ID"]
    del os.environ["REDDIT_CLIENT_SECRET"]
    del os.environ["DEBUG_MODE"]
    del os.environ["RANDOM_SEED"]

def test_load_config_from_file():
    """Test loading config from a JSON file."""
    config_data = {
        "api_keys": {
            "pushshift_api_key": "file_key",
            "reddit_client_id": "file_id",
            "reddit_client_secret": "file_secret"
        },
        "dataset_paths": {
            "raw_dir": "custom/raw",
            "processed_dir": "custom/processed"
        },
        "debug_mode": True,
        "random_seed": 999
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = load_config_from_file(temp_path)
        
        assert config.api_keys.pushshift_api_key == "file_key"
        assert config.api_keys.reddit_client_id == "file_id"
        assert config.dataset_paths.raw_dir == Path("custom/raw")
        assert config.debug_mode is True
        assert config.random_seed == 999
    finally:
        os.unlink(temp_path)

def test_load_config_from_file_missing_file():
    """Test loading config from a non-existent file returns defaults."""
    config = load_config_from_file("non_existent_file.json")
    assert config.random_seed == 42
    assert config.debug_mode is False

def test_load_config_from_file_invalid_json():
    """Test that invalid JSON raises an error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        with pytest.raises(json.JSONDecodeError):
            load_config_from_file(temp_path)
    finally:
        os.unlink(temp_path)

def test_get_config_singleton():
    """Test that get_config returns the same instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2

def test_config_paths_exist():
    """Test that dataset paths created by Config exist."""
    config = Config()
    assert config.dataset_paths.raw_dir.exists()
    assert config.dataset_paths.processed_dir.exists()