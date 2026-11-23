import pytest
import tempfile
import os
from pathlib import Path
import yaml

from checksum_verification import (
    calculate_sha256,
    verify_sparc_data_integrity,
    update_metadata_with_verification
)

def test_calculate_sha256():
    """Test SHA256 calculation on a known file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_sha256(temp_path)
        # SHA256 of "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_verify_sparc_data_integrity_empty_dir():
    """Test verification on empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        results = verify_sparc_data_integrity(data_dir)
        assert results["all_passed"] is False
        assert len(results["files"]) == 0

def test_verify_sparc_data_integrity_single_file():
    """Test verification on single file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        test_file = data_dir / "test.txt"
        test_file.write_text("test data")
        
        results = verify_sparc_data_integrity(data_dir)
        assert results["all_passed"] is True
        assert "test.txt" in results["files"]
        assert results["files"]["test.txt"]["status"] == "verified"

def test_update_metadata_with_verification():
    """Test metadata update with verification results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / "metadata.yaml"
        
        # Create initial metadata
        initial_metadata = {
            "project": {"name": "test"},
            "data": {"source": "test"}
        }
        with open(metadata_path, 'w') as f:
            yaml.dump(initial_metadata, f)
        
        verification_results = {
            "verified_at": "2024-01-01T00:00:00",
            "all_passed": True,
            "files": {"test.zip": {"checksum": "abc123", "status": "verified"}}
        }
        
        update_metadata_with_verification(metadata_path, verification_results)
        
        with open(metadata_path, 'r') as f:
            updated_metadata = yaml.safe_load(f)
        
        assert "verification" in updated_metadata["data"]
        assert updated_metadata["data"]["verification"]["all_passed"] is True
        assert "last_verified" in updated_metadata["data"]