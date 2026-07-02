import os
import json
import tempfile
import pytest
from pathlib import Path

# Import the functions from utils
# Note: In a real test environment, we might mock the network calls
# but here we test the logic with local files
try:
    from code.utils import compute_sha256, verify_checksums, write_manifest, DatasetManifest
except ImportError:
    # Fallback if run from different directory structure
    import sys
    sys.path.insert(0, 'code')
    from utils import compute_sha256, verify_checksums, write_manifest, DatasetManifest

def test_compute_sha256():
    """Test SHA-256 computation on a known file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        hash_val = compute_sha256(temp_path)
        # Expected hash for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_val == expected, f"Hash mismatch: {hash_val} != {expected}"
    finally:
        os.unlink(temp_path)

def test_compute_sha256_missing_file():
    """Test SHA-256 on a non-existent file."""
    hash_val = compute_sha256("/nonexistent/path/file.txt")
    assert hash_val == "file_not_found"

def test_verify_checksums_integration(tmp_path):
    """Test the full checksum verification flow."""
    # Setup
    manifest_dir = tmp_path / "raw"
    manifest_dir.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    
    # Create a dummy file
    dummy_file = manifest_dir / "test_eeg.bdf"
    dummy_file.write_text("dummy data")
    
    # Create a manifest
    manifest_data = {
        "dataset_id": "test_ds",
        "status": "verified",
        "eeg_present": True,
        "questionnaire_present": False,
        "file_paths": ["test_eeg.bdf"],
        "error_message": None
    }
    manifest_path = manifest_dir / "dataset_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    
    checksum_output = state_dir / "checksums.json"
    
    # Run verification
    result = verify_checksums(str(manifest_path), str(checksum_output))
    
    # Assertions
    assert "test_eeg.bdf" in result
    assert result["test_eeg.bdf"] != "missing"
    assert result["test_eeg.bdf"] != "file_not_found"
    
    # Verify file was written
    assert checksum_output.exists()
    with open(checksum_output, 'r') as f:
        written_data = json.load(f)
    assert "test_eeg.bdf" in written_data

def test_verify_checksums_missing_file_in_manifest(tmp_path):
    """Test checksum verification when a file in manifest is missing."""
    manifest_dir = tmp_path / "raw"
    manifest_dir.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    
    # Create manifest with a missing file
    manifest_data = {
        "dataset_id": "test_ds",
        "status": "partial",
        "eeg_present": False,
        "questionnaire_present": False,
        "file_paths": ["missing_file.bdf"],
        "error_message": None
    }
    manifest_path = manifest_dir / "dataset_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    
    checksum_output = state_dir / "checksums.json"
    
    result = verify_checksums(str(manifest_path), str(checksum_output))
    
    assert result["missing_file.bdf"] == "missing"
