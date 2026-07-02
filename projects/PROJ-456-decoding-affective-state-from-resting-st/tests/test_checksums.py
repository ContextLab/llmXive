import json
import os
import pathlib
import tempfile
import pytest
from code.utils import compute_sha256, verify_checksums, DatasetManifest

def test_compute_sha256():
    """Test SHA-256 computation on a temporary file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        hash_val = compute_sha256(temp_path)
        assert len(hash_val) == 64  # SHA-256 hex length
        assert isinstance(hash_val, str)
    finally:
        os.unlink(temp_path)

def test_verify_checksums_creates_file():
    """Test that verify_checksums creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        
        # Create a fake manifest
        manifest_path = tmpdir / "manifest.json"
        test_file = tmpdir / "data.txt"
        test_file.write_text("test content")
        
        manifest_data = [
            {
                "dataset_id": "test_ds",
                "dataset_path": str(tmpdir),
                "verification_status": "verified",
                "file_count": 1,
                "total_size_bytes": 12,
                "eeg_present": True,
                "questionnaire_present": True
            }
        ]
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        checksum_path = tmpdir / "checksums.json"
        
        # Run verification
        result = verify_checksums(str(manifest_path), str(checksum_path))
        
        # Assertions
        assert checksum_path.exists()
        assert str(test_file) in result
        assert len(result[str(test_file)]) == 64
        
        # Verify file content
        with open(checksum_path, 'r') as f:
            saved_checksums = json.load(f)
        assert str(test_file) in saved_checksums

def test_verify_checksums_missing_manifest():
    """Test that verify_checksums raises error for missing manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            verify_checksums(
                os.path.join(tmpdir, "nonexistent.json"),
                os.path.join(tmpdir, "checksums.json")
            )
