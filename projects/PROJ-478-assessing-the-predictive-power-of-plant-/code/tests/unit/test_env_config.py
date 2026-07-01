"""
Unit tests for environment configuration and checksum verification.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from src.utils.env_config import (
    compute_file_checksum,
    verify_checksum,
    register_checksum,
    verify_all_downloads,
    load_environment_config
)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "test_data.txt"
    content = b"Hello, World! This is test data for checksum verification."
    file_path.write_bytes(content)
    return file_path, content


@pytest.fixture
def temp_manifest_dir(tmp_path):
    """Create a temporary directory structure for testing manifests."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    return raw_dir


def test_compute_file_checksum(temp_file):
    """Test checksum computation."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content).hexdigest()
    computed_hash = compute_file_checksum(str(file_path))
    assert computed_hash == expected_hash


def test_compute_file_checksum_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum("/nonexistent/path/file.txt")


def test_verify_checksum_success(temp_file):
    """Test successful checksum verification."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content).hexdigest()
    assert verify_checksum(str(file_path), expected_hash) is True


def test_verify_checksum_failure(temp_file):
    """Test failed checksum verification."""
    file_path, _ = temp_file
    assert verify_checksum(str(file_path), "invalid_checksum") is False


def test_register_checksum(temp_manifest_dir):
    """Test registering a checksum."""
    # Create a file
    test_file = temp_manifest_dir / "test_register.txt"
    test_file.write_bytes(b"test content")
    
    # Temporarily override module constants for testing
    import src.utils.env_config as env_config
    original_manifest = env_config.CHECKSUM_MANIFEST_FILE
    original_raw = env_config.DATA_RAW_DIR
    
    try:
        env_config.CHECKSUM_MANIFEST_FILE = str(temp_manifest_dir / "checksums.json")
        env_config.DATA_RAW_DIR = str(temp_manifest_dir)
        
        # Register
        register_checksum(str(test_file))
        
        # Verify manifest exists and contains entry
        manifest_path = Path(env_config.CHECKSUM_MANIFEST_FILE)
        assert manifest_path.exists()
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        assert "test_register.txt" in manifest
        assert "checksum" in manifest["test_register.txt"]
        assert manifest["test_register.txt"]["algorithm"] == "sha256"
    finally:
        # Restore constants
        env_config.CHECKSUM_MANIFEST_FILE = original_manifest
        env_config.DATA_RAW_DIR = original_raw


def test_verify_all_downloads(temp_manifest_dir):
    """Test verifying all downloads."""
    # Create a file and register it
    test_file = temp_manifest_dir / "verify_test.txt"
    test_file.write_bytes(b"verify content")
    
    import src.utils.env_config as env_config
    original_manifest = env_config.CHECKSUM_MANIFEST_FILE
    original_raw = env_config.DATA_RAW_DIR
    
    try:
        env_config.CHECKSUM_MANIFEST_FILE = str(temp_manifest_dir / "checksums.json")
        env_config.DATA_RAW_DIR = str(temp_manifest_dir)
        
        # Register
        register_checksum(str(test_file))
        
        # Verify
        results = verify_all_downloads()
        
        assert len(results) == 1
        assert "verify_test.txt" in results
        assert results["verify_test.txt"] is True
    finally:
        env_config.CHECKSUM_MANIFEST_FILE = original_manifest
        env_config.DATA_RAW_DIR = original_raw


def test_load_environment_config(monkeypatch):
    """Test loading environment configuration."""
    # Set a known value
    monkeypatch.setenv("GBIF_API_KEY", "test_key_123")
    monkeypatch.setenv("MAX_WORKERS", "8")
    
    config = load_environment_config()
    
    assert config["GBIF_API_KEY"] == "test_key_123"
    assert config["MAX_WORKERS"] == "8"
    # Check default for unset value
    assert config["WORLDCLIM_BASE_URL"] is not None
