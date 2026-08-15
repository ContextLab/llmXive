"""
Validation tests to ensure the hash implementation meets the specification.
"""
import pytest
import tempfile
from pathlib import Path
from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest

def test_fr_hash_001_single_file_hashing():
    """Validate FR-HASH-001: Single file hashing with large file simulation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "large_file.bin"
        # Create a 1MB file to simulate chunked reading
        with open(file_path, "wb") as f:
            f.write(b"X" * (1024 * 1024))
        
        hash_val = calculate_sha256(file_path)
        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)

def test_fr_hash_002_manifest_generation():
    """Validate FR-HASH-002: Manifest generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "f1.txt").write_bytes(b"1")
        (root / "f2.txt").write_bytes(b"2")
        
        manifest_path = root / "manifest.json"
        generate_manifest([root / "f1.txt", root / "f2.txt"], output_path=manifest_path)
        
        assert manifest_path.exists()
        import json
        with open(manifest_path) as f:
            data = json.load(f)
        assert "f1.txt" in data
        assert "f2.txt" in data

def test_fr_hash_003_manifest_verification():
    """Validate FR-HASH-003: Manifest verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        f1 = root / "f1.txt"
        f1.write_bytes(b"data")
        
        import json
        import hashlib
        manifest = {
            "f1.txt": hashlib.sha256(b"data").hexdigest()
        }
        (root / "manifest.json").write_text(json.dumps(manifest))
        
        assert verify_manifest(root / "manifest.json") is True
        
        # Corrupt file
        f1.write_bytes(b"corrupt")
        assert verify_manifest(root / "manifest.json") is False

def test_fr_hash_004_error_handling():
    """Validate FR-HASH-004: Error handling."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(Path("/nonexistent"))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            calculate_sha256(Path(tmpdir))