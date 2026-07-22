import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open

from src.data_loader import (
    load_manifest,
    verify_checksum,
    download_file,
    fetch_dataset,
    fetch_datasets_by_source,
    validate_manifest,
    get_cached_datasets,
    clear_cache,
    create_default_manifest,
    DATA_ROOT
)

class TestManifestLoading:
    def test_load_manifest_creates_default(self, tmp_path):
        # Mock DATA_ROOT to use tmp_path
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            manifest = load_manifest()
            assert "datasets" in manifest
            assert len(manifest["datasets"]) > 0

    def test_load_manifest_existing(self, tmp_path):
        test_manifest = {"datasets": [{"id": "test", "source": "GEO", "url": "http://test.com", "checksum": "abc"}]}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(test_manifest, f)
        
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            manifest = load_manifest()
            assert manifest == test_manifest

class TestChecksumVerification:
    def test_verify_checksum_sha256(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello")
        # SHA256 of "hello"
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        assert verify_checksum(file_path, expected) is True
        assert verify_checksum(file_path, "wrong") is False

    def test_verify_checksum_md5(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello")
        # MD5 of "hello"
        expected = "5d41402abc4b2a76b9719d911017c592"
        assert verify_checksum(file_path, expected, "md5") is True

    def test_verify_checksum_missing_file(self, tmp_path):
        file_path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            verify_checksum(file_path, "abc")

class TestManifestValidation:
    def test_validate_manifest_valid(self, tmp_path):
        test_manifest = {"datasets": [{"id": "1", "source": "GEO", "url": "u", "checksum": "c"}]}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(test_manifest, f)
        
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            assert validate_manifest() is True

    def test_validate_manifest_missing_key(self, tmp_path):
        test_manifest = {"datasets": [{"id": "1"}]}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(test_manifest, f)
        
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            assert validate_manifest() is False

class TestDatasetFetching:
    @patch('src.data_loader.download_file')
    def test_fetch_dataset_existing(self, mock_download, tmp_path):
        test_manifest = {"datasets": [{"id": "GSE1", "source": "GEO", "url": "http://x", "checksum": "c"}]}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(test_manifest, f)
        
        # Create a dummy file
        dummy_file = tmp_path / "raw" / "GSE1.csv"
        dummy_file.parent.mkdir()
        dummy_file.write_text("data")
        
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            result = fetch_dataset("GSE1")
            assert result == dummy_file
            mock_download.assert_not_called()

    @patch('src.data_loader.download_file')
    def test_fetch_dataset_download(self, mock_download, tmp_path):
        test_manifest = {"datasets": [{"id": "GSE2", "source": "GEO", "url": "http://x", "checksum": "c"}]}
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(test_manifest, f)
        
        mock_download.return_value = tmp_path / "raw" / "GSE2.csv"
        
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            result = fetch_dataset("GSE2")
            mock_download.assert_called_once()
            assert result == tmp_path / "raw" / "GSE2.csv"

class TestUrlValidation:
    def test_fetch_datasets_by_source(self, tmp_path):
        test_manifest = {
            "datasets": [
                {"id": "G1", "source": "GEO", "url": "u", "checksum": "c"},
                {"id": "T1", "source": "TCGA", "url": "u", "checksum": "c"}
            ]
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(test_manifest, f)
        
        # Mock fetch_dataset to return a path
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            with patch('src.data_loader.fetch_dataset') as mock_fetch:
                mock_fetch.return_value = tmp_path / "raw" / "G1.csv"
                paths = fetch_datasets_by_source("GEO")
                assert len(paths) == 1
                mock_fetch.assert_called_with("G1")

class TestCacheManagement:
    def test_get_cached_datasets(self, tmp_path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        (raw_dir / "file1.csv").touch()
        (raw_dir / "file2.csv").touch()
        
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            paths = get_cached_datasets()
            assert len(paths) == 2

    def test_clear_cache(self, tmp_path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        (raw_dir / "file1.csv").touch()
        
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            clear_cache()
            assert not (raw_dir / "file1.csv").exists()
            assert raw_dir.exists()

class TestDefaultManifestCreation:
    def test_create_default_manifest(self, tmp_path):
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            create_default_manifest()
            manifest_path = tmp_path / "manifest.json"
            assert manifest_path.exists()
            with open(manifest_path) as f:
                data = json.load(f)
                assert "datasets" in data
                assert len(data["datasets"]) > 0

class TestIntegration:
    @patch('src.data_loader.requests.get')
    def test_download_file_real_mock(self, mock_get, tmp_path):
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test"]
        mock_response.headers = {"content-length": "4"}
        mock_get.return_value.__enter__.return_value = mock_response
        mock_get.return_value.raise_for_status = MagicMock()
        
        dest = tmp_path / "test.txt"
        with patch('src.data_loader.DATA_ROOT', tmp_path):
            result = download_file("http://test.com", dest, expected_checksum=None)
            assert result.exists()
            assert result.read_bytes() == b"test"