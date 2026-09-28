import os
import sys
import tempfile
import yaml
import hashlib
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.finalize_state_registry import (
    compute_sha256,
    compute_directory_hash,
    collect_all_artifact_hashes,
    update_state_registry
)

def test_compute_sha256_file():
    """Test SHA-256 computation for a file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        # Compute expected hash manually
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        actual_hash = compute_sha256(temp_path)
        
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_compute_sha256_empty_file():
    """Test SHA-256 computation for an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        temp_path = f.name
    
    try:
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(temp_path)
        
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_compute_directory_hash():
    """Test directory hash computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("content1")
        
        file2 = Path(tmpdir) / "file2.txt"
        file2.write_text("content2")
        
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"
        file3.write_text("content3")
        
        # Compute hash
        dir_hash = compute_directory_hash(tmpdir)
        
        # Should be a valid hex string
        assert len(dir_hash) == 64
        assert all(c in '0123456789abcdef' for c in dir_hash)

def test_compute_directory_hash_deterministic():
    """Test that directory hash is deterministic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("content1")
        
        file2 = Path(tmpdir) / "file2.txt"
        file2.write_text("content2")
        
        # Compute hash twice
        hash1 = compute_directory_hash(tmpdir)
        hash2 = compute_directory_hash(tmpdir)
        
        assert hash1 == hash2

def test_collect_all_artifact_hashes():
    """Test collection of artifact hashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("content1")
        
        file2 = Path(tmpdir) / "file2.txt"
        file2.write_text("content2")
        
        hashes = collect_all_artifact_hashes(tmpdir)
        
        assert len(hashes) == 2
        assert "file1.txt" in hashes
        assert "file2.txt" in hashes

def test_update_state_registry():
    """Test updating state registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create state file
        state_file = Path(tmpdir) / "state.yaml"
        initial_state = {
            "project_id": "test-project",
            "artifact_hashes": {"existing": "hash123"}
        }
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Create data directory
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        (data_dir / "test.txt").write_text("test")
        
        # Update registry
        success = update_state_registry(str(state_file), str(data_dir))
        
        assert success
        
        # Verify update
        with open(state_file, 'r') as f:
            updated_state = yaml.safe_load(f)
        
        assert 'reproducibility_hash' in updated_state
        assert 'final_verification_timestamp' in updated_state
        assert len(updated_state['reproducibility_hash']) == 64
        assert 'artifact_hashes' in updated_state

def test_update_state_registry_nonexistent_file():
    """Test updating non-existent state file."""
    success = update_state_registry("/nonexistent/path/state.yaml", "/nonexistent/data")
    assert not success

def test_update_state_registry_invalid_yaml():
    """Test updating file with invalid YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create invalid YAML
        state_file = Path(tmpdir) / "state.yaml"
        state_file.write_text("invalid: yaml: content: [")
        
        # Create data directory
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        
        success = update_state_registry(str(state_file), str(data_dir))
        assert not success