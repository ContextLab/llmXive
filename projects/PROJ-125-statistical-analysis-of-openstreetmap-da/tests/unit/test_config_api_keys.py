"""
Unit tests for API key rotation and secure storage logic in config.py (T040).
"""
import os
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the functions we're testing
from config import (
    register_api_key,
    rotate_api_key,
    check_key_expiration,
    validate_api_key,
    get_api_key_status,
    generate_key_report,
    _load_key_metadata,
    _save_key_metadata,
    _get_key_hash,
    KEY_ROTATION_THRESHOLD_SECONDS,
    KEY_METADATA_PATH
)

@pytest.fixture
def temp_metadata_dir(tmp_path):
    """Create a temporary directory for metadata files."""
    # Mock the KEY_METADATA_PATH to use temp directory
    original_path = KEY_METADATA_PATH
    temp_path = tmp_path / "key_metadata.json"
    
    # Patch the global variable in the config module
    import config
    config.KEY_METADATA_PATH = temp_path
    
    yield temp_path
    
    # Restore original path
    config.KEY_METADATA_PATH = original_path

@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "OVERPASS_API_KEY": "test_overpass_key_123",
        "AWS_ACCESS_KEY": "test_aws_key_456"
    }):
        yield

def test_get_key_hash():
    """Test that key hashing produces consistent results."""
    key = "test_key"
    hash1 = _get_key_hash(key)
    hash2 = _get_key_hash(key)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
    assert hash1 != key  # Hash should not be the original key

def test_register_api_key(temp_metadata_dir):
    """Test registering a new API key."""
    service = "OVERPASS"
    key = "test_key_123"
    
    result = register_api_key(service, key)
    
    assert result is True
    
    # Verify metadata was saved
    metadata = _load_key_metadata()
    assert service in metadata
    assert "versions" in metadata[service]
    assert len(metadata[service]["versions"]) == 1
    
    # Verify hash is stored (not the key itself)
    stored_hash = metadata[service]["versions"][0]["hash"]
    assert stored_hash == _get_key_hash(key)
    assert stored_hash != key

def test_rotate_api_key(temp_metadata_dir):
    """Test rotating an API key creates a new version."""
    service = "OVERPASS"
    old_key = "old_key_123"
    new_key = "new_key_456"
    
    # Register old key
    register_api_key(service, old_key)
    
    # Rotate to new key
    result = rotate_api_key(service, new_key)
    
    assert result is True
    
    # Verify new version was added
    metadata = _load_key_metadata()
    assert len(metadata[service]["versions"]) == 2
    
    # Verify most recent version is the new key
    latest_hash = metadata[service]["versions"][0]["hash"]
    assert latest_hash == _get_key_hash(new_key)

def test_key_version_limit(temp_metadata_dir):
    """Test that only last 3 versions are kept."""
    service = "OVERPASS"
    
    # Register 5 keys
    for i in range(5):
        register_api_key(service, f"key_{i}")
    
    metadata = _load_key_metadata()
    assert len(metadata[service]["versions"]) == 3

def test_check_key_expiration_new_key(temp_metadata_dir):
    """Test that a newly registered key is not expired."""
    service = "OVERPASS"
    key = "test_key"
    
    register_api_key(service, key)
    
    is_expired, msg = check_key_expiration(service)
    
    assert is_expired is False
    assert "valid" in msg.lower()

def test_check_key_expiration_expired_key(temp_metadata_dir):
    """Test that an old key is marked as expired."""
    service = "OVERPASS"
    key = "test_key"
    
    # Register key
    register_api_key(service, key)
    
    # Manually set timestamp to be old
    metadata = _load_key_metadata()
    old_timestamp = int(time.time()) - (KEY_ROTATION_THRESHOLD_SECONDS + 1000)
    metadata[service]["versions"][0]["registered_at"] = old_timestamp
    _save_key_metadata(metadata)
    
    is_expired, msg = check_key_expiration(service)
    
    assert is_expired is True
    assert "expired" in msg.lower() or "old" in msg.lower()

def test_check_key_expiration_no_key(temp_metadata_dir):
    """Test expiration check when no key is registered."""
    service = "NONEXISTENT"
    
    is_expired, msg = check_key_expiration(service)
    
    assert is_expired is True
    assert "no registered key" in msg.lower()

def test_validate_api_key_valid(mock_env_vars, temp_metadata_dir):
    """Test validation of a valid API key."""
    service = "OVERPASS"
    
    # Register the key
    register_api_key(service, os.getenv("OVERPASS_API_KEY"))
    
    is_valid, msg = validate_api_key(service)
    
    assert is_valid is True
    assert "valid" in msg.lower()

def test_validate_api_key_missing_env(mock_env_vars, temp_metadata_dir):
    """Test validation when env var is missing."""
    service = "AWS"
    
    # Remove AWS key from env
    with patch.dict(os.environ, {}, clear=False):
        del os.environ["AWS_ACCESS_KEY"]
        
        is_valid, msg = validate_api_key(service)
        
        assert is_valid is False
        assert "not set" in msg.lower()

def test_validate_api_key_expired(mock_env_vars, temp_metadata_dir):
    """Test validation of an expired key."""
    service = "OVERPASS"
    
    # Register key
    register_api_key(service, os.getenv("OVERPASS_API_KEY"))
    
    # Make it expired
    metadata = _load_key_metadata()
    old_timestamp = int(time.time()) - (KEY_ROTATION_THRESHOLD_SECONDS + 1000)
    metadata[service]["versions"][0]["registered_at"] = old_timestamp
    _save_key_metadata(metadata)
    
    is_valid, msg = validate_api_key(service)
    
    assert is_valid is False
    assert "failed" in msg.lower()

def test_get_api_key_status(mock_env_vars, temp_metadata_dir):
    """Test getting status of all keys."""
    # Register keys
    register_api_key("OVERPASS", os.getenv("OVERPASS_API_KEY"))
    register_api_key("AWS", os.getenv("AWS_ACCESS_KEY"))
    
    status = get_api_key_status()
    
    assert "OVERPASS" in status
    assert "AWS" in status
    assert "key_exists" in status["OVERPASS"]
    assert "is_expired" in status["OVERPASS"]
    assert "message" in status["OVERPASS"]

def test_generate_key_report(mock_env_vars, temp_metadata_dir):
    """Test generating a key status report."""
    # Register keys
    register_api_key("OVERPASS", os.getenv("OVERPASS_API_KEY"))
    
    report = generate_key_report()
    
    assert "API Key Status Report" in report
    assert "OVERPASS" in report
    assert len(report) > 0