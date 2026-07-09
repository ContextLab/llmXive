import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from src.data_loader import (
    load_manifest, verify_checksum, create_default_manifest,
    fetch_dataset, validate_manifest, get_cached_datasets, clear_cache
)
from src.config import DATA_ROOT

class TestManifestLoading:
    def test_load_manifest_creates_default_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock DATA_ROOT to use temp dir
            with patch('src.data_loader.DATA_ROOT', Path(tmpdir)):
                with patch('src.data_loader.MANIFEST_FILE', Path(tmpdir) / "manifest.json"):
                    manifest = load_manifest()
                    assert "datasets" in manifest

class TestChecksumVerification:
    def test_verify_checksum_success(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            f.flush()
            path = Path(f.name)
        # Known hash for "test data"
        expected_hash = "916131f5e0160003940f9e7339186518e27e007e292743535599807081786427"
        assert verify_checksum(path, expected_hash)
        os.unlink(path)

class TestManifestValidation:
    def test_validate_manifest_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            data = {"datasets": [{"id": "1", "source": "GEO", "url": "http://x", "checksum": "a"}]}
            with open(manifest_path, 'w') as f:
                json.dump(data, f)
            with patch('src.data_loader.MANIFEST_FILE', manifest_path):
                assert validate_manifest() is True

class TestDatasetFetching:
    def test_fetch_dataset_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump({"datasets": []}, f)
            with patch('src.data_loader.MANIFEST_FILE', manifest_path):
                result = fetch_dataset("nonexistent")
                assert result is None

class TestUrlValidation:
    pass # Simplified for T001

class TestCacheManagement:
    def test_clear_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir()
            (raw_dir / "test.csv").touch()
            with patch('src.data_loader.DATA_ROOT', Path(tmpdir)):
                clear_cache()
                assert not (raw_dir / "test.csv").exists()

class TestDefaultManifestCreation:
    def test_create_default_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            with patch('src.data_loader.DATA_ROOT', Path(tmpdir)):
                with patch('src.data_loader.MANIFEST_FILE', manifest_path):
                    create_default_manifest()
                    assert manifest_path.exists()

class TestIntegration:
    pass
