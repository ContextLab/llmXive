import pytest
from pathlib import Path
import tempfile
import yaml
from checksum_manager import (
    calculate_file_sha256,
    load_project_state,
    save_project_state,
    update_artifact_hash,
    verify_artifact_integrity
)

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    checksum = calculate_file_sha256(temp_path)
    assert len(checksum) == 64  # SHA256 hex length
    assert checksum == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    
    temp_path.unlink()

def test_update_artifact_hash():
    """Test updating artifact hash in state."""
    state = {"project_id": "test", "artifact_hashes": {}}
    state = update_artifact_hash(state, "data/raw/test.fasta", "abc123")
    
    assert "data/raw/test.fasta" in state["artifact_hashes"]
    assert state["artifact_hashes"]["data/raw/test.fasta"] == "abc123"

def test_verify_artifact_integrity():
    """Test artifact integrity verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test content")
        temp_path = Path(f.name)
    
    checksum = calculate_file_sha256(temp_path)
    state = {"artifact_hashes": {str(temp_path): checksum}}
    
    assert verify_artifact_integrity(state, str(temp_path)) is True
    
    # Test mismatch
    state["artifact_hashes"][str(temp_path)] = "wrong_checksum"
    assert verify_artifact_integrity(state, str(temp_path)) is False
    
    temp_path.unlink()

def test_load_save_project_state():
    """Test loading and saving project state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        original_state = {
            "project_id": "test-proj",
            "artifact_hashes": {"data/raw/file.txt": "hash123"}
        }
        
        save_project_state(state_path, original_state)
        loaded_state = load_project_state(state_path)
        
        assert loaded_state["project_id"] == original_state["project_id"]
        assert loaded_state["artifact_hashes"] == original_state["artifact_hashes"]