import pytest
import json
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import based on project structure
# Assuming tests are run from root and code/ is in sys.path or installed
try:
    from download_data import compute_file_hash, validate_checksum, save_dataset
except ImportError:
    # Fallback for direct execution in tests/
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from download_data import compute_file_hash, validate_checksum, save_dataset


class TestComputeFileHash:
    def test_compute_sha256_hash(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)
        
        try:
            hash_val = compute_file_hash(temp_path)
            # Manual calculation
            expected = hashlib.sha256(b"Hello, World!").hexdigest()
            assert hash_val == expected
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            compute_file_hash(Path("non_existent_file.txt"))


class TestSaveDataset:
    def test_save_dataset_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            data = [{"id": 1, "text": "test"}]
            
            save_dataset(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == data


class TestValidateChecksum:
    def test_create_new_checksum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.json"
            checksum_path = Path(tmpdir) / "checksums.json"
            
            data = [{"id": 1}]
            save_dataset(data, data_path)
            
            # Should create checksum file and return True
            result = validate_checksum(data_path, checksum_path)
            assert result is True
            assert checksum_path.exists()
            
            with open(checksum_path, 'r') as f:
                stored = json.load(f)
            assert "hash" in stored
            assert stored["algorithm"] == "sha256"

    def test_valid_checksum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.json"
            checksum_path = Path(tmpdir) / "checksums.json"
            
            data = [{"id": 1}]
            save_dataset(data, data_path)
            
            # Create initial checksum
            validate_checksum(data_path, checksum_path)
            
            # Verify again
            result = validate_checksum(data_path, checksum_path)
            assert result is True

    def test_invalid_checksum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.json"
            checksum_path = Path(tmpdir) / "checksums.json"
            
            # Create data
            save_dataset([{"id": 1}], data_path)
            
            # Create fake checksum file with wrong hash
            wrong_hash = "0" * 64
            checksum_data = {
                "file": "data.json",
                "algorithm": "sha256",
                "hash": wrong_hash
            }
            with open(checksum_path, 'w') as f:
                json.dump(checksum_data, f)
            
            # Should return False
            result = validate_checksum(data_path, checksum_path)
            assert result is False
