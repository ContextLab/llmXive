"""
Unit tests for versioning.py
"""
import os
import tempfile
import yaml
import hashlib
from pathlib import Path
from datetime import datetime
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from versioning import compute_sha256, compute_directory_hash, load_state, save_state, update_version_state, invalidate_stale_reviews

def test_compute_sha256():
    """Test SHA-256 computation for a file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash1 = compute_sha256(temp_path)
        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 == hashlib.sha256(b"test content").hexdigest()
        
        # Ensure same content produces same hash
        hash2 = compute_sha256(temp_path)
        assert hash1 == hash2
    finally:
        temp_path.unlink()

def test_compute_directory_hash():
    """Test directory hashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create some files
        (tmpdir_path / "file1.txt").write_text("content1")
        (tmpdir_path / "file2.txt").write_text("content2")
        subdir = tmpdir_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        hashes = compute_directory_hash(tmpdir_path)
        
        assert "file1.txt" in hashes
        assert "file2.txt" in hashes
        assert "subdir/file3.txt" in hashes
        assert len(hashes) == 3

def test_load_state_nonexistent():
    """Test loading non-existent state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "nonexistent.yaml"
        state = load_state(state_file)
        assert state == {}

def test_save_and_load_state():
    """Test saving and loading state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        test_state = {
            "project": "TEST-123",
            "artifacts": {"file.txt": {"hash": "abc123"}}
        }
        
        save_state(test_state, state_file)
        assert state_file.exists()
        
        loaded = load_state(state_file)
        assert loaded["project"] == "TEST-123"
        assert loaded["artifacts"]["file.txt"]["hash"] == "abc123"

def test_invalidate_stale_reviews_no_changes():
    """Test invalidation when no artifacts changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        reviews_file = Path(tmpdir) / "reviews.yaml"
        reviews_data = {
            "records": [
                {"id": "R1", "artifacts": ["file1.txt"], "status": "approved"},
                {"id": "R2", "artifacts": ["file2.txt"], "status": "pending"}
            ]
        }
        with open(reviews_file, 'w') as f:
            yaml.dump(reviews_data, f)
        
        current_hashes = {
            "file1.txt": {"hash": "abc123"},
            "file2.txt": {"hash": "def456"}
        }
        previous_hashes = {
            "file1.txt": {"hash": "abc123"},
            "file2.txt": {"hash": "def456"}
        }
        
        invalidated = invalidate_stale_reviews(current_hashes, previous_hashes, reviews_file)
        
        assert len(invalidated) == 0
        
        # Verify records are still valid
        with open(reviews_file, 'r') as f:
            updated = yaml.safe_load(f)
        assert updated["records"][0]["status"] == "approved"

def test_invalidate_stale_reviews_with_changes():
    """Test invalidation when artifacts changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        reviews_file = Path(tmpdir) / "reviews.yaml"
        reviews_data = {
            "records": [
                {"id": "R1", "artifacts": ["file1.txt"], "status": "approved"},
                {"id": "R2", "artifacts": ["file2.txt"], "status": "pending"},
                {"id": "R3", "artifacts": ["file1.txt", "file2.txt"], "status": "approved"}
            ]
        }
        with open(reviews_file, 'w') as f:
            yaml.dump(reviews_data, f)
        
        current_hashes = {
            "file1.txt": {"hash": "new_hash_123"},  # Changed
            "file2.txt": {"hash": "def456"}
        }
        previous_hashes = {
            "file1.txt": {"hash": "old_hash_456"},
            "file2.txt": {"hash": "def456"}
        }
        
        invalidated = invalidate_stale_reviews(current_hashes, previous_hashes, reviews_file)
        
        # R1 and R3 should be invalidated because they reference file1.txt
        assert len(invalidated) == 2
        assert "R1" in invalidated
        assert "R3" in invalidated
        assert "R2" not in invalidated
        
        # Verify status updates in file
        with open(reviews_file, 'r') as f:
            updated = yaml.safe_load(f)
        
        for record in updated["records"]:
            if record["id"] in ["R1", "R3"]:
                assert record["status"] == "invalidated"
                assert "invalidation_reason" in record
                assert "file1.txt" in record["invalidation_reason"]

def test_update_version_state_integration(tmp_path):
    """Integration test for full update_version_state flow."""
    # Create project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "data").mkdir()
    (project_root / "data" / "raw").mkdir()
    (project_root / "code").mkdir()
    (project_root / "code" / "test.py").write_text("print('hello')")
    
    state_file = project_root / "state.yaml"
    reviews_file = project_root / "reviews.yaml"
    
    # Initial state
    initial_state = {
        "project": "TEST",
        "artifacts": {"code/test.py": {"hash": "old_hash"}}
    }
    with open(state_file, 'w') as f:
        yaml.dump(initial_state, f)
    
    reviews_data = {
        "records": [
            {"id": "R1", "artifacts": ["code/test.py"], "status": "approved"}
        ]
    }
    with open(reviews_file, 'w') as f:
        yaml.dump(reviews_data, f)
    
    # Run update
    state = update_version_state(
        targets=["code"],
        state_file=state_file,
        reviews_file=reviews_file,
        project_root=project_root
    )
    
    assert state["project"] == "TEST-786-multi-property-trade-offs-in-alloy-desig"
    assert "code" in state["artifacts"]
    assert "last_updated" in state
    
    # Verify invalidation happened
    assert "last_invalidation" in state
    assert state["last_invalidation"]["records_invalidated"] == 1
    assert "R1" in state["last_invalidation"]["invalidated_ids"]
    
    # Verify reviews file updated
    with open(reviews_file, 'r') as f:
        updated_reviews = yaml.safe_load(f)
    assert updated_reviews["records"][0]["status"] == "invalidated"
