import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Mock config to avoid dependency on full project setup for unit tests
# We will test the logic functions directly by patching paths if necessary,
# but for T006 we are mostly testing the helper logic which is path-agnostic
# if we pass Path objects directly.

# However, since the functions use get_path, we need to ensure the test
# environment has a valid config or mock get_path.
# For this specific task, we will test the core hashing and registry logic
# by creating a temporary directory structure and mocking the registry path.

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.checksum_tracker import (
    compute_file_checksum,
    load_registry,
    save_registry,
    register_file,
    verify_file,
    initialize_directories,
)
from code.utils.common import save_json, load_json

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking data/raw and data/processed."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    registry_dir = tmp_path / "data" / "registry"
    
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    registry_dir.mkdir(parents=True)
    
    # Create a test file
    test_file = raw_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    # Create a registry file
    registry_file = registry_dir / "checksums.json"
    registry_file.write_text('{"files": {}}')
    
    return {
        "root": tmp_path,
        "raw": raw_dir,
        "processed": processed_dir,
        "registry": registry_dir,
        "registry_file": registry_file,
        "test_file": test_file
    }

def test_compute_file_checksum(temp_data_dir):
    """Test SHA-256 checksum computation."""
    file_path = temp_data_dir["test_file"]
    checksum = compute_file_checksum(file_path)
    
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length
    
    # Verify consistency
    checksum2 = compute_file_checksum(file_path)
    assert checksum == checksum2

def test_compute_file_checksum_nonexistent():
    """Test checksum computation on non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))

def test_register_file(temp_data_dir, monkeypatch):
    """Test file registration."""
    # Monkeypatch get_path to use temp directory
    from code import utils
    from code.utils import checksum_tracker
    
    original_get_path = checksum_tracker.get_path
    
    def mock_get_path(*args):
        if args[0] == "data":
            return temp_data_dir["root"] / "data" / args[1]
        return original_get_path(*args)
    
    monkeypatch.setattr(checksum_tracker, "get_path", mock_get_path)
    
    file_path = temp_data_dir["test_file"]
    result = register_file(file_path, "Test Description")
    
    assert result is True
    
    # Verify registry was updated
    registry = load_json(temp_data_dir["registry_file"])
    rel_path = str(file_path.relative_to(temp_data_dir["root"] / "data"))
    
    assert rel_path in registry["files"]
    assert registry["files"][rel_path]["checksum"] == compute_file_checksum(file_path)
    assert registry["files"][rel_path]["description"] == "Test Description"

def test_verify_file_valid(temp_data_dir, monkeypatch):
    """Test verification of a valid file."""
    from code import utils
    from code.utils import checksum_tracker
    
    original_get_path = checksum_tracker.get_path
    def mock_get_path(*args):
        if args[0] == "data":
            return temp_data_dir["root"] / "data" / args[1]
        return original_get_path(*args)
    monkeypatch.setattr(checksum_tracker, "get_path", mock_get_path)
    
    file_path = temp_data_dir["test_file"]
    
    # First register it
    register_file(file_path)
    
    # Then verify
    assert verify_file(file_path) is True

def test_verify_file_mismatch(temp_data_dir, monkeypatch):
    """Test verification fails on content change."""
    from code import utils
    from code.utils import checksum_tracker
    
    original_get_path = checksum_tracker.get_path
    def mock_get_path(*args):
        if args[0] == "data":
            return temp_data_dir["root"] / "data" / args[1]
        return original_get_path(*args)
    monkeypatch.setattr(checksum_tracker, "get_path", mock_get_path)
    
    file_path = temp_data_dir["test_file"]
    
    # Register
    register_file(file_path)
    
    # Modify content
    file_path.write_text("Modified Content")
    
    # Verify should fail
    assert verify_file(file_path) is False

def test_initialize_directories(temp_data_dir, monkeypatch):
    """Test directory initialization."""
    from code import utils
    from code.utils import checksum_tracker
    
    original_get_path = checksum_tracker.get_path
    def mock_get_path(*args):
        if args[0] == "data":
            return temp_data_dir["root"] / "data" / args[1]
        return original_get_path(*args)
    monkeypatch.setattr(checksum_tracker, "get_path", mock_get_path)
    
    # Remove registry to simulate fresh start
    temp_data_dir["registry_file"].unlink()
    
    initialize_directories()
    
    assert temp_data_dir["registry_file"].exists()
    
    registry = load_json(temp_data_dir["registry_file"])
    assert "files" in registry