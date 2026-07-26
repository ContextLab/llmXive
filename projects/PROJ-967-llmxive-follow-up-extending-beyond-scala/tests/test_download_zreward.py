import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_zreward import calculate_sha256, verify_checksum, save_checksum

def test_calculate_sha256():
    """Test SHA256 calculation on a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = tmp.name

    try:
        checksum = calculate_sha256(tmp_path)
        assert len(checksum) == 64  # SHA256 hex string length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(tmp_path)

def test_save_and_verify_checksum():
    """Test saving and verifying checksums."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp_file:
        tmp_file.write("test content")
        file_path = tmp_file.name

    checksum_dir = tempfile.mkdtemp()
    checksum_file = os.path.join(checksum_dir, "checksums.csv")

    try:
        checksum = calculate_sha256(file_path)
        save_checksum(checksum, file_path, checksum_file)

        # Verify correct checksum
        is_valid, msg = verify_checksum(file_path, checksum_file)
        assert is_valid is True

        # Verify incorrect checksum
        with open(checksum_file, 'w') as f:
            f.write(f"{os.path.basename(file_path)},wrong_checksum\n")

        is_valid, msg = verify_checksum(file_path, checksum_file)
        assert is_valid is False
        assert "mismatch" in msg.lower()
    finally:
        os.unlink(file_path)
        os.unlink(checksum_file)
        os.rmdir(checksum_dir)

def test_download_dataset_raises_on_failure(monkeypatch):
    """Test that download_dataset raises RuntimeError when all sources fail."""
    from download_zreward import download_dataset
    import logging

    # Mock load_dataset to always raise an exception
    def mock_load_dataset(*args, **kwargs):
        raise Exception("Simulated network failure")

    monkeypatch.setattr("download_zreward.load_dataset", mock_load_dataset)

    logger = logging.getLogger("test")
    
    with pytest.raises(RuntimeError) as excinfo:
        download_dataset(logger)
    
    assert "Failed to download dataset" in str(excinfo.value)