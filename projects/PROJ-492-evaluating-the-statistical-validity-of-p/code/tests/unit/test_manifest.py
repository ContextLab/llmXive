"""
Unit tests for manifest generation (T014).
Verifies that manifest.json is created with SHA256 hashes.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.src.utils.manifest import generate_manifest, compute_sha256

@pytest.fixture
def temp_dirs():
    """Create temporary directories for output and data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        data_dir = tmp_path / "data"
        output_dir.mkdir()
        data_dir.mkdir()
        
        # Create some dummy files
        (output_dir / "test.json").write_text('{"key": "value"}')
        (data_dir / "raw.csv").write_text("col1,col2\n1,2")
        
        yield output_dir, data_dir, tmp_path

def test_compute_sha256():
    """Test SHA256 computation on a known string."""
    content = "test content"
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
        f.flush()
        path = Path(f.name)
    
    try:
        hash_val = compute_sha256(path)
        # Known hash for "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert hash_val == expected
    finally:
        os.unlink(path)

def test_generate_manifest_creates_file(temp_dirs):
    """Test that generate_manifest creates the manifest file."""
    output_dir, data_dir, tmp_path = temp_dirs
    manifest_path = output_dir / "manifest.json"
    
    manifest = generate_manifest(output_dir, data_dir, manifest_path)
    
    assert manifest_path.exists()
    assert "artifacts" in manifest
    assert "generated_at" in manifest
    assert len(manifest["artifacts"]) >= 2  # At least the two dummy files

def test_manifest_contains_sha256_hashes(temp_dirs):
    """Test that manifest entries contain valid SHA256 hashes."""
    output_dir, data_dir, tmp_path = temp_dirs
    manifest_path = output_dir / "manifest.json"
    
    generate_manifest(output_dir, data_dir, manifest_path)
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    for rel_path, info in data["artifacts"].items():
        assert "sha256" in info
        assert len(info["sha256"]) == 64  # SHA256 hex length
        # Verify it's a valid hex string
        int(info["sha256"], 16)

def test_manifest_hash_matches_content(temp_dirs):
    """Test that the hash in manifest matches the actual file content."""
    output_dir, data_dir, tmp_path = temp_dirs
    manifest_path = output_dir / "manifest.json"
    
    # Modify a file after creation to ensure we are testing the current state
    test_file = output_dir / "test.json"
    test_file.write_text("modified content")
    
    generate_manifest(output_dir, data_dir, manifest_path)
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Find the test.json entry
    found = False
    for rel_path, info in data["artifacts"].items():
        if "test.json" in str(rel_path):
            found = True
            expected_hash = compute_sha256(test_file)
            assert info["sha256"] == expected_hash
            break
    
    assert found, "test.json not found in manifest"