import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.data.download_jsvulndb import (
    compute_sha256_file,
    load_checksums,
    save_checksums,
    update_global_checksums,
    download_file,
    ensure_output_dir
)

class TestDownloadJSVulnDB:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_ensure_output_dir(self, temp_dir):
        new_dir = temp_dir / "subdir" / "nested"
        ensure_output_dir(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_compute_sha256_file(self, temp_dir):
        test_file = temp_dir / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256_file(test_file)
        
        assert actual_hash == expected_hash

    def test_load_checksums_empty(self, temp_dir):
        checksums_path = temp_dir / "checksums.json"
        result = load_checksums(checksums_path)
        assert result == {}

    def test_save_and_load_checksums(self, temp_dir):
        checksums_path = temp_dir / "checksums.json"
        test_data = {"file1.txt": "abc123", "file2.txt": "def456"}
        
        save_checksums(checksums_path, test_data)
        loaded = load_checksums(checksums_path)
        
        assert loaded == test_data

    def test_update_global_checksums(self, temp_dir):
        checksums_path = temp_dir / "checksums.json"
        initial_data = {"existing.txt": "oldhash"}
        save_checksums(checksums_path, initial_data)
        
        update_global_checksums(checksums_path, "new.txt", "newhash")
        
        final_data = load_checksums(checksums_path)
        assert "existing.txt" in final_data
        assert final_data["existing.txt"] == "oldhash"
        assert "new.txt" in final_data
        assert final_data["new.txt"] == "newhash"

    @patch('src.data.download_jsvulndb.requests.get')
    def test_download_file_success(self, mock_get, temp_dir):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        url = "http://example.com/file.txt"
        dest = temp_dir / "file.txt"
        
        success = download_file(url, dest)
        
        assert success is True
        assert dest.exists()
        assert dest.read_bytes() == b"chunk1chunk2"

    @patch('src.data.download_jsvulndb.requests.get')
    def test_download_file_failure(self, mock_get, temp_dir):
        mock_get.side_effect = Exception("Network error")
        
        url = "http://example.com/file.txt"
        dest = temp_dir / "file.txt"
        
        success = download_file(url, dest)
        
        assert success is False
        assert not dest.exists()
