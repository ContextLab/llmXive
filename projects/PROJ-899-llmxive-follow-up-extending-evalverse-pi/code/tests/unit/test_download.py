import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

class TestComputeSha256:
    def test_sha256_computation(self):
        from src.data.download import compute_sha256
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = Path(f.name)
        
        checksum = compute_sha256(temp_path)
        assert len(checksum) == 64 # SHA256 hex length
        os.unlink(temp_path)

class TestEnsureDirectories:
    def test_directories_creation(self):
        from src.data.download import ensure_directories
        # This should not raise
        ensure_directories()

class TestChecksumFunctions:
    def test_save_and_load_checksum(self):
        from src.data.download import save_checksum, load_stored_checksum
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        
        save_checksum("abc123", temp_path)
        loaded = load_stored_checksum(temp_path)
        assert loaded == "abc123"
        os.unlink(temp_path)

class TestDataAvailability:
    def test_is_data_available_false(self):
        from src.data.download import is_data_available
        # Assuming empty raw dir initially
        assert not is_data_available()
