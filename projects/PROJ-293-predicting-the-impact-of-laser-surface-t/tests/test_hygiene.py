"""
Tests for code/hygiene.py
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml
import hashlib

# Import the module under test
from hygiene import (
    calculate_md5,
    get_file_metadata,
    load_artifact_hashes,
    save_artifact_hashes,
    update_artifact_hash,
    verify_artifact_integrity,
    register_multiple_artifacts,
    cleanup_stale_hashes,
    get_artifact_status,
    STATE_DIR,
    ARTIFACT_HASH_FILE
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content for hygiene")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_registry_file():
    """Create a temporary registry file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        f.write("last_updated: '2024-01-01T00:00:00'\nartifacts: {}\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_calculate_md5(temp_file):
    """Test MD5 calculation."""
    content = b"test content for hygiene"
    expected_hash = hashlib.md5(content).hexdigest()
    actual_hash = calculate_md5(temp_file)
    assert actual_hash == expected_hash


def test_calculate_md5_file_not_found():
    """Test MD5 calculation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_md5("non_existent_file.txt")


def test_calculate_md5_directory(tmp_path):
    """Test MD5 calculation on directory."""
    with pytest.raises(ValueError):
        calculate_md5(tmp_path)


def test_get_file_metadata(temp_file):
    """Test file metadata extraction."""
    metadata = get_file_metadata(temp_file)
    assert "size_bytes" in metadata
    assert "modified_time" in metadata
    assert "extension" in metadata
    assert "filename" in metadata
    assert metadata["extension"] == ".txt"


def test_load_artifact_hashes_missing_file(tmp_path, monkeypatch):
    """Test loading hash registry when file doesn't exist."""
    # Temporarily change the constant
    monkeypatch.setattr("hygiene.STATE_DIR", tmp_path)
    monkeypatch.setattr("hygiene.ARTIFACT_HASH_FILE", tmp_path / "artifact_hashes.yaml")
    
    registry = load_artifact_hashes()
    assert "last_updated" in registry
    assert "artifacts" in registry
    assert registry["artifacts"] == {}


def test_save_artifact_hashes(tmp_path, monkeypatch):
    """Test saving hash registry."""
    # Setup
    monkeypatch.setattr("hygiene.STATE_DIR", tmp_path)
    monkeypatch.setattr("hygiene.ARTIFACT_HASH_FILE", tmp_path / "artifact_hashes.yaml")
    
    data = {
        "last_updated": "2024-01-01T00:00:00",
        "artifacts": {
            "test.txt": {"md5": "abc123", "metadata": {}, "updated_at": "2024-01-01"}
        }
    }
    
    save_artifact_hashes(data)
    
    # Verify
    assert (tmp_path / "artifact_hashes.yaml").exists()
    with open(tmp_path / "artifact_hashes.yaml", "r") as f:
        loaded = yaml.safe_load(f)
    assert loaded["artifacts"]["test.txt"]["md5"] == "abc123"


def test_update_artifact_hash(temp_file):
    """Test updating artifact hash in registry."""
    registry = {"artifacts": {}}
    updated = update_artifact_hash(temp_file, registry)
    
    assert len(updated["artifacts"]) == 1
    key = list(updated["artifacts"].keys())[0]
    assert "md5" in updated["artifacts"][key]
    assert "metadata" in updated["artifacts"][key]
    assert "updated_at" in updated["artifacts"][key]


def test_verify_artifact_integrity_success(temp_file):
    """Test successful integrity verification."""
    hash_val = calculate_md5(temp_file)
    is_valid, msg = verify_artifact_integrity(temp_file, hash_val)
    assert is_valid
    assert "verified" in msg.lower()


def test_verify_artifact_integrity_failure(temp_file):
    """Test failed integrity verification."""
    is_valid, msg = verify_artifact_integrity(temp_file, "wrong_hash")
    assert not is_valid
    assert "mismatch" in msg.lower()


def test_verify_artifact_integrity_missing():
    """Test integrity verification on missing file."""
    is_valid, msg = verify_artifact_integrity("non_existent.txt", "any_hash")
    assert not is_valid
    assert "not found" in msg.lower()


def test_register_multiple_artifacts(temp_file):
    """Test registering multiple artifacts."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write("second file")
        temp_file2 = f2.name
    
    try:
        registry = {"artifacts": {}}
        updated = register_multiple_artifacts([temp_file, temp_file2], registry)
        assert len(updated["artifacts"]) == 2
    finally:
        os.unlink(temp_file2)


def test_cleanup_stale_hashes():
    """Test cleanup of stale artifacts."""
    from datetime import datetime, timedelta
    
    old_date = (datetime.now() - timedelta(days=60)).isoformat()
    new_date = datetime.now().isoformat()
    
    registry = {
        "artifacts": {
            "old.txt": {"updated_at": old_date},
            "new.txt": {"updated_at": new_date}
        }
    }
    
    cleaned = cleanup_stale_hashes(registry, threshold_days=30)
    assert len(cleaned["artifacts"]) == 1
    assert "new.txt" in cleaned["artifacts"]


def test_get_artifact_status_new(temp_file, tmp_path, monkeypatch):
    """Test status for new artifact."""
    monkeypatch.setattr("hygiene.STATE_DIR", tmp_path)
    monkeypatch.setattr("hygiene.ARTIFACT_HASH_FILE", tmp_path / "artifact_hashes.yaml")
    
    registry = {"artifacts": {}}
    status = get_artifact_status(temp_file, registry)
    assert status["status"] == "new"
    assert status["exists"]


def test_get_artifact_status_unchanged(temp_file, tmp_path, monkeypatch):
    """Test status for unchanged artifact."""
    monkeypatch.setattr("hygiene.STATE_DIR", tmp_path)
    monkeypatch.setattr("hygiene.ARTIFACT_HASH_FILE", tmp_path / "artifact_hashes.yaml")
    
    hash_val = calculate_md5(temp_file)
    registry = {
        "artifacts": {
            str(Path(temp_file).relative_to(Path.cwd())): {"md5": hash_val}
        }
    }
    
    status = get_artifact_status(temp_file, registry)
    assert status["status"] == "unchanged"


def test_get_artifact_status_missing(tmp_path, monkeypatch):
    """Test status for missing artifact."""
    monkeypatch.setattr("hygiene.STATE_DIR", tmp_path)
    monkeypatch.setattr("hygiene.ARTIFACT_HASH_FILE", tmp_path / "artifact_hashes.yaml")
    
    registry = {"artifacts": {}}
    status = get_artifact_status("non_existent.txt", registry)
    assert status["status"] == "missing"
    assert not status["exists"]
