import hashlib
import json
import tempfile
from pathlib import Path
import pytest

from code.src.utils.manifest import compute_sha256, generate_manifest

def test_compute_sha256():
    """Test that compute_sha256 returns the correct hash for a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash, "SHA256 hash mismatch."
    finally:
        temp_path.unlink()

def test_generate_manifest_structure():
    """Test that generate_manifest returns a dict with the correct structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        test_file = output_dir / "test.json"
        test_file.write_text("{}")
        
        files_to_hash = [test_file]
        manifest = generate_manifest(files_to_hash, output_dir)
        
        assert isinstance(manifest, dict)
        assert "files" in manifest
        assert isinstance(manifest["files"], list)
        assert len(manifest["files"]) == 1
        
        file_entry = manifest["files"][0]
        assert "name" in file_entry
        assert "sha256" in file_entry
        assert "size" in file_entry

def test_manifest_contains_correct_hashes():
    """Test that the hashes in the manifest match the actual file hashes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        test_file = output_dir / "data.txt"
        content = "Some data for hashing"
        test_file.write_text(content)
        
        files_to_hash = [test_file]
        manifest = generate_manifest(files_to_hash, output_dir)
        
        actual_hash = hashlib.sha256(content.encode()).hexdigest()
        manifest_hash = manifest["files"][0]["sha256"]
        
        assert actual_hash == manifest_hash, "Manifest hash does not match actual file hash."