import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import json

# Import the functions to test
from download import calculate_md5, validate_checksum, get_checksum_from_manifest

def test_calculate_md5():
    """Test MD5 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test data")
        temp_path = f.name
    
    try:
        # "test data" MD5 is known
        expected_md5 = hashlib.md5(b"test data").hexdigest()
        actual_md5 = calculate_md5(temp_path)
        assert actual_md5 == expected_md5
    finally:
        os.unlink(temp_path)

def test_validate_checksum_success():
    """Test successful checksum validation."""
    content = b"validation test content"
    expected_md5 = hashlib.md5(content).hexdigest()
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.fits') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # Should not raise
        result = validate_checksum(temp_path, expected_md5)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_validate_checksum_failure():
    """Test checksum validation failure raises error."""
    content = b"wrong content"
    expected_md5 = hashlib.md5(b"different content").hexdigest()
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.fits') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            validate_checksum(temp_path, expected_md5)
    finally:
        os.unlink(temp_path)

def test_get_checksum_from_manifest():
    """Test reading checksum from manifest."""
    manifest_data = {
        "files": {
            "test.fits": {
                "md5": "abc123def456",
                "url": "http://example.com/test.fits"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(manifest_data, f)
        temp_path = f.name
    
    try:
        checksum = get_checksum_from_manifest("test.fits", temp_path)
        assert checksum == "abc123def456"
        
        # Test missing file
        missing = get_checksum_from_manifest("missing.fits", temp_path)
        assert missing is None
    finally:
        os.unlink(temp_path)

def test_validate_checksum_file_not_found():
    """Test validation fails if file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        validate_checksum("/nonexistent/path/file.fits", "abc123")