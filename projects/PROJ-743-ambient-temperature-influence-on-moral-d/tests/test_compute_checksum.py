import os
import sys
import hashlib
import tempfile
import yaml
from pathlib import Path
import pytest

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from compute_checksum import compute_sha256, update_state_file, ensure_state_file_exists

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_compute_sha256(temp_dir):
    test_file = temp_dir / "test.txt"
    content = b"Hello, world!"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(test_file)
    
    assert actual_hash == expected_hash

def test_compute_sha256_missing_file(temp_dir):
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        compute_sha256(missing_file)

def test_update_state_file(temp_dir):
    state_file = temp_dir / "state.yaml"
    key = "test_key"
    value = "test_value"
    
    update_state_file(state_file, key, value)
    
    assert state_file.exists()
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "artifact_hashes" in data
    assert data["artifact_hashes"][key] == value
    assert "updated_at" in data
    assert data["updated_at"] is not None

def test_ensure_state_file_exists_creates_file(temp_dir):
    state_file = temp_dir / "new_state.yaml"
    assert not state_file.exists()
    
    ensure_state_file_exists(state_file)
    
    assert state_file.exists()
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "artifact_hashes" in data
    assert "updated_at" in data