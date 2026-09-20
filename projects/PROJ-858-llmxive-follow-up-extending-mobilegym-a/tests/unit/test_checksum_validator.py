import json
import hashlib
import tempfile
import os
from pathlib import Path
import pytest

from utils.checksum_validator import calculate_sha256, verify_artifact, run_validation

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_sha256(temp_path)
        expected = hashlib.sha256(b"test content").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_verify_artifact_missing_file():
    """Test verification of a missing file."""
    is_valid, message = verify_artifact(Path("/nonexistent/file.txt"), "abc123", "nonexistent/file.txt")
    assert not is_valid
    assert "missing" in message.lower()

def test_verify_artifact_checksum_mismatch():
    """Test verification when checksums don't match."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        is_valid, message = verify_artifact(temp_path, "wrong_checksum", "test/file.txt")
        assert not is_valid
        assert "mismatch" in message.lower()
    finally:
        os.unlink(temp_path)

def test_verify_artifact_success():
    """Test successful verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        checksum = hashlib.sha256(b"test content").hexdigest()
        is_valid, message = verify_artifact(temp_path, checksum, "test/file.txt")
        assert is_valid
        assert "verified" in message.lower()
    finally:
        os.unlink(temp_path)

def test_run_validation_empty_registry():
    """Test validation with an empty registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        with open(registry_path, "w") as f:
            json.dump({}, f)
        
        # This should return True because there are no artifacts to validate
        result = run_validation(registry_path)
        assert result is True

def test_run_validation_with_missing_artifacts():
    """Test validation when artifacts are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        registry = {
            "nonexistent/file.txt": "abc123"
        }
        with open(registry_path, "w") as f:
            json.dump(registry, f)
        
        result = run_validation(registry_path)
        assert result is False
