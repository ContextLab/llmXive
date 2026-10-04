import pytest
import os
import yaml
from pathlib import Path
from code.data_loader import compute_and_store_hashes, compute_sha256, ARTIFACT_HASHES_FILE, STATE_DIR

def test_compute_sha256():
    """Test that compute_sha256 returns a valid hex string."""
    # Create a temp file
    test_file = Path("tests/tmp_test_file.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("test content")
    
    hash_val = compute_sha256(test_file)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in hash_val)
    
    test_file.unlink()

def test_compute_and_store_hashes():
    """Test that hashes are computed and written to the state file."""
    # Run the computation
    hashes = compute_and_store_hashes()
    
    # Verify the file exists
    assert ARTIFACT_HASHES_FILE.exists(), "Artifact hashes file should be created."
    
    # Verify the content is valid YAML and contains expected keys
    with open(ARTIFACT_HASHES_FILE, 'r') as f:
        content = yaml.safe_load(f)
    
    assert isinstance(content, dict), "Artifact hashes should be a dictionary."
    assert len(content) > 0, "At least one hash should be computed."
    
    # Verify at least one key is a synthetic file or manifest
    keys = list(content.keys())
    assert any("synthetic" in k or "manifest" in k for k in keys), "Should contain synthetic or manifest hash."

def test_hash_consistency():
    """Test that the same file produces the same hash."""
    test_file = Path("tests/tmp_consistency_test.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("consistent content")
    
    hash1 = compute_sha256(test_file)
    hash2 = compute_sha256(test_file)
    
    assert hash1 == hash2, "Hash should be consistent for the same file."
    
    test_file.unlink()
