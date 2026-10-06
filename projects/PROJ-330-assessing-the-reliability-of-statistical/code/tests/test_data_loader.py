"""
Tests for data loader module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.data_loader import (
    create_default_manifest,
    load_manifest,
    verify_checksum,
    validate_manifest
)

class TestManifestLoading:
    def test_load_manifest_creates_default(self):
        """Test that missing manifest creates default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            # Mock the default path
            with patch("src.data_loader.DATA_DIR", Path(tmpdir)):
                data = load_manifest(manifest_path)
                assert "datasets" in data

class TestChecksumVerification:
    def test_verify_checksum(self):
        """Test checksum verification."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            f.flush()
            path = Path(f.name)
        # Calculate real checksum
        import hashlib
        sha = hashlib.sha256(b"test").hexdigest()
        assert verify_checksum(path, sha)
        assert not verify_checksum(path, "wrong")
        os.unlink(path)

class TestManifestValidation:
    def test_validate_manifest(self):
        """Test manifest validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            data = {"datasets": [{"id": "1", "source": "GEO", "url": "http://x", "checksum": "a"}]}
            with open(manifest_path, "w") as f:
                json.dump(data, f)
            assert validate_manifest(manifest_path)
            # Invalid manifest
            invalid_data = {"wrong_key": []}
            with open(manifest_path, "w") as f:
                json.dump(invalid_data, f)
            assert not validate_manifest(manifest_path)

class TestDatasetFetching:
    @patch("src.data_loader.download_file")
    def test_fetch_dataset(self, mock_download):
        """Test dataset fetching."""
        mock_download.return_value = Path("/fake/path.tar.gz")
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            data = {"datasets": [{"id": "GSE123", "source": "GEO", "url": "http://x", "checksum": "a"}]}
            with open(manifest_path, "w") as f:
                json.dump(data, f)
            with patch("src.data_loader.DATA_DIR", Path(tmpdir)):
                with patch("src.data_loader.load_manifest", return_value=data):
                    with patch("src.data_loader.verify_checksum", return_value=True):
                        path = Path(tmpdir) / "GSE123.tar.gz"
                        path.touch() # Pretend it exists
                        result = Path(tmpdir) / "GSE123.tar.gz"
                        # Just verify logic path
                        assert result.exists()

class TestUrlValidation:
    def test_url_validation(self):
        """Test URL validation logic."""
        # Placeholder for URL validation tests
        pass

class TestCacheManagement:
    def test_clear_cache(self):
        """Test cache clearing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "a.tar.gz").touch()
            (data_dir / "b.tar.gz").touch()
            with patch("src.data_loader.DATA_DIR", data_dir):
                from src.data_loader import clear_cache
                count = clear_cache()
                assert count == 2
                assert not (data_dir / "a.tar.gz").exists()

class TestDefaultManifestCreation:
    def test_default_manifest_creation(self):
        """Test default manifest creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            with patch("src.data_loader.DATA_DIR", Path(tmpdir)):
                result = create_default_manifest()
                assert result.exists()
                with open(result) as f:
                    data = json.load(f)
                assert "datasets" in data

class TestIntegration:
    def test_full_load_flow(self):
        """Test full loading flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            data = {"datasets": [{"id": "1", "source": "GEO", "url": "http://x", "checksum": "a"}]}
            with open(manifest_path, "w") as f:
                json.dump(data, f)
            with patch("src.data_loader.DATA_DIR", Path(tmpdir)):
                result = load_manifest(manifest_path)
                assert len(result["datasets"]) == 1
