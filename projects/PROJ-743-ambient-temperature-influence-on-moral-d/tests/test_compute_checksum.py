import os
import hashlib
import tempfile
import yaml
from pathlib import Path
import pytest

# Import the functions to test
# Note: In a real scenario, we might need to adjust the import path if running from tests/
# For now, assuming standard PYTHONPATH setup or relative import handling by pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from compute_checksum import compute_sha256, ensure_state_file_exists, update_state_file

def test_compute_sha256_valid_file():
    """Test that compute_sha256 returns the correct hash for a known file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello, World!")
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_compute_sha256_file_not_found():
    """Test that compute_sha256 raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")

def test_ensure_state_file_exists_creates_new():
    """Test that ensure_state_file_exists creates a new file with correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        
        result_path = ensure_state_file_exists(str(state_path))
        
        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "project_id" in data
        assert "created_at" in data
        assert "checksums" in data
        assert data["checksums"] == {}

def test_ensure_state_file_exists_uses_existing():
    """Test that ensure_state_file_exists does not overwrite existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        
        # Create initial file
        initial_data = {"project_id": "TEST-001", "checksums": {"existing": "value"}}
        with open(state_path, 'w') as f:
            yaml.dump(initial_data, f)
        
        result_path = ensure_state_file_exists(str(state_path))
        
        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["project_id"] == "TEST-001"
        assert "existing" in data["checksums"]

def test_update_state_file():
    """Test that update_state_file correctly adds a checksum entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        file_path = Path(tmpdir) / "test_file.txt"
        
        # Create dummy file
        file_path.write_text("test data")
        
        # Initialize state
        ensure_state_file_exists(str(state_path))
        
        # Update with checksum
        checksum = hashlib.sha256(b"test data").hexdigest()
        update_state_file(str(state_path), str(file_path), checksum)
        
        # Verify
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check that the checksum was recorded (key might be relative path)
        assert "checksums" in data
        assert len(data["checksums"]) == 1
        
        # Verify the value
        entry = list(data["checksums"].values())[0]
        assert entry["algorithm"] == "sha256"
        assert entry["value"] == checksum
        assert "recorded_at" in entry