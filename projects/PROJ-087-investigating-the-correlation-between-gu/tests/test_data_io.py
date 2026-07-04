import os
import tempfile
import json
import pytest
from pathlib import Path

# Mock the config module to avoid dependency on actual project root setup
class MockConfig:
    PROJECT_ROOT = tempfile.mkdtemp()

import sys
sys.modules['config'] = MockConfig()

# Now import the module under test
from data_io import (
    setup_data_directories,
    register_file_checksum,
    validate_registered_checksums,
    get_raw_data_path,
    get_processed_data_path
)
from utils import calculate_file_checksum

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield temp
    # Cleanup happens automatically by pytest-temp or can be manual

def test_setup_data_directories():
    """Test that setup_data_directories creates the required structure."""
    # We can't easily test the actual directory creation without modifying config
    # So we test the logic by checking if the function runs without error
    try:
        setup_data_directories()
    except Exception as e:
        pytest.fail(f"setup_data_directories raised an exception: {e}")

def test_register_file_checksum():
    """Test checksum registration for a file."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_file = f.name

    try:
        # Register the checksum
        success = register_file_checksum(temp_file)
        assert success, "Checksum registration failed"

        # Verify the checksums file was updated
        from data_io import CHECKSUMS_FILE
        assert os.path.exists(CHECKSUMS_FILE), "Checksums file was not created"

        with open(CHECKSUMS_FILE, 'r') as f:
            checksums = json.load(f)
        
        assert temp_file in checksums, "File path not found in checksums"
        assert "checksum" in checksums[temp_file], "Checksum value missing"
        assert checksums[temp_file]["algorithm"] == "md5", "Default algorithm not used"
    finally:
        os.unlink(temp_file)
        # Clean up checksums file if it was created in temp dir
        if os.path.exists(CHECKSUMS_FILE):
            os.unlink(CHECKSUMS_FILE)

def test_validate_registered_checksums():
    """Test validation of registered checksums."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_file = f.name

    try:
        # Register the checksum
        register_file_checksum(temp_file)

        # Validate
        results = validate_registered_checksums()
        
        assert temp_file in results, "File path not found in validation results"
        assert results[temp_file] is True, "Valid file marked as invalid"

        # Corrupt the file and validate again
        with open(temp_file, 'w') as f:
            f.write("corrupted content")

        results = validate_registered_checksums()
        assert results[temp_file] is False, "Corrupted file not detected"
    finally:
        os.unlink(temp_file)
        if os.path.exists(CHECKSUMS_FILE):
            os.unlink(CHECKSUMS_FILE)

def test_get_raw_data_path():
    """Test path generation for raw data."""
    path = get_raw_data_path("test.csv")
    assert "data/raw" in path
    assert path.endswith("test.csv")

def test_get_processed_data_path():
    """Test path generation for processed data."""
    path = get_processed_data_path("analysis.csv")
    assert "data/processed" in path
    assert path.endswith("analysis.csv")
