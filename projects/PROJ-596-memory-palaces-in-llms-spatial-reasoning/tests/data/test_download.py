import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import hashlib

# Mock the datasets library to avoid heavy downloads during unit tests
# We test the logic of checksum computation and file handling
from unittest.mock import patch, MagicMock, mock_open

# Adjust import path to project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data.download import compute_file_checksum, get_dataset_cache_paths, save_checksums

class TestChecksums:
    def test_compute_file_checksum(self, tmp_path):
        """Test SHA-256 computation on a known string."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        result = compute_file_checksum(test_file)
        
        assert result == expected_hash
        assert len(result) == 64  # SHA-256 hex length

    def test_compute_file_checksum_large(self, tmp_path):
        """Test with a larger file to ensure chunking works."""
        test_file = tmp_path / "large.txt"
        content = b"0123456789" * 10000  # 100KB
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        result = compute_file_checksum(test_file)
        
        assert result == expected_hash

class TestSaveChecksums:
    def test_save_checksums_creates_file(self, tmp_path):
        """Test that save_checksums writes a valid JSON file."""
        # Mock the PROJECT_ROOT and CHECKSUMS_FILE behavior
        # We patch the module-level variables or pass a custom path
        
        # Since the function uses global CHECKSUMS_FILE, we need to mock the path
        # or temporarily change the working directory.
        # A better approach for this specific design is to mock the file write.
        
        test_data = [
            {
                "dataset": "test_dataset",
                "config": "test_config",
                "files": [{"file": "test.json", "sha256": "abc123"}]
            }
        ]
        
        # Create a temporary file path for the test
        output_file = tmp_path / "checksums.json"
        
        # Patch the global variable logic by passing the path directly? 
        # The current implementation uses a global CHECKSUMS_FILE.
        # We will patch the Path object used inside the function.
        
        import code.data.download as download_module
        
        original_path = download_module.CHECKSUMS_FILE
        download_module.CHECKSUMS_FILE = output_file
        
        try:
            save_checksums(test_data)
            
            assert output_file.exists()
            with open(output_file, "r") as f:
                data = json.load(f)
            
            assert "datasets" in data
            assert len(data["datasets"]) == 1
            assert data["datasets"][0]["dataset"] == "test_dataset"
        finally:
            download_module.CHECKSUMS_FILE = original_path

class TestGetCachePaths:
    def test_get_cache_paths_empty(self, tmp_path):
        """Test when cache directory is empty."""
        # Mock the HF_DATASETS_CACHE environment variable to point to tmp_path
        with patch.dict(os.environ, {"HF_DATASETS_CACHE": str(tmp_path)}):
            # Also need to mock the internal config if it doesn't use env var
            with patch("code.data.download.hf_config.HF_DATASETS_CACHE", str(tmp_path)):
                paths = get_dataset_cache_paths("nonexistent_dataset")
                assert paths == []

    def test_get_cache_paths_found(self, tmp_path):
        """Test when cache files exist."""
        # Create a fake cache structure
        cache_dir = tmp_path / "datasets" / "babi" / "task3_10k" / "v1.0"
        cache_dir.mkdir(parents=True)
        fake_file = cache_dir / "dataset_cache.arrow"
        fake_file.write_text("fake data")
        
        with patch.dict(os.environ, {"HF_DATASETS_CACHE": str(tmp_path)}):
            with patch("code.data.download.hf_config.HF_DATASETS_CACHE", str(tmp_path)):
                paths = get_dataset_cache_paths("babi", "task3_10k")
                assert len(paths) == 1
                assert "babi" in str(paths[0])
                assert "task3_10k" in str(paths[0])
                assert fake_file in paths

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
