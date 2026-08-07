"""
Unit tests for the data ingestion module.
Tests URL validation, checksumming, and download logic.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import requests_mock
from src.data.ingestion import (
    IngestionError,
    validate_url,
    compute_sha256,
    download_file,
    load_csv_robust,
    DatasetManifest,
    create_manifest,
    load_manifest
)


class TestURLValidation:
    """Tests for URL validation logic."""

    def test_valid_http_url(self):
        url = "http://example.com/data.csv"
        assert validate_url(url) is True

    def test_valid_https_url(self):
        url = "https://example.com/data.csv"
        assert validate_url(url) is True

    def test_invalid_protocol(self):
        url = "ftp://example.com/data.csv"
        with pytest.raises(IngestionError, match="Invalid protocol"):
            validate_url(url)

    def test_empty_url(self):
        with pytest.raises(IngestionError, match="URL must be a non-empty string"):
            validate_url("")

    def test_none_url(self):
        with pytest.raises(IngestionError, match="URL must be a non-empty string"):
            validate_url(None)

    def test_missing_domain(self):
        url = "https:///data.csv"
        with pytest.raises(IngestionError, match="URL must have a valid domain"):
            validate_url(url)

    def test_missing_path(self):
        url = "https://example.com"
        with pytest.raises(IngestionError, match="URL must have a path component"):
            validate_url(url)


class TestChecksum:
    """Tests for SHA256 checksum computation."""

    def test_compute_sha256(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            expected = hashlib.sha256(b"test data").hexdigest()
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_nonexistent_file(self):
        with pytest.raises(IngestionError, match="Failed to compute checksum"):
            compute_sha256("/nonexistent/file.txt")


class TestDownloadFile:
    """Tests for file download logic."""

    def test_download_success(self):
        with requests_mock.Mocker() as m:
            m.get("https://example.com/data.csv", text="col1,col2\n1,2\n3,4")
            with tempfile.TemporaryDirectory() as tmpdir:
                dest = Path(tmpdir) / "data.csv"
                result_path = download_file("https://example.com/data.csv", dest)

                assert result_path.exists()
                assert result_path.stat().st_size > 0

    def test_download_failure_invalid_url(self):
        with pytest.raises(IngestionError, match="Invalid protocol"):
            download_file("ftp://example.com/data.csv", "/tmp/data.csv")

    def test_download_failure_network_error(self):
        with requests_mock.Mocker() as m:
            m.get("https://example.com/data.csv", exc=Exception("Network error"))
            with tempfile.TemporaryDirectory() as tmpdir:
                dest = Path(tmpdir) / "data.csv"
                with pytest.raises(IngestionError, match="Network error"):
                    download_file("https://example.com/data.csv", dest)

    def test_download_failure_empty_response(self):
        with requests_mock.Mocker() as m:
            m.get("https://example.com/data.csv", text="")
            with tempfile.TemporaryDirectory() as tmpdir:
                dest = Path(tmpdir) / "data.csv"
                with pytest.raises(IngestionError, match="file is empty"):
                    download_file("https://example.com/data.csv", dest)


class TestLoadCSVRobust:
    """Tests for robust CSV loading."""

    def test_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("date,value\n2020-01-01,10\n2020-01-02,20")
            temp_path = f.name

        try:
            df = load_csv_robust(temp_path)
            assert len(df) == 2
            assert 'value' in df.columns
        finally:
            os.unlink(temp_path)

    def test_load_empty_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(IngestionError, match="empty"):
                load_csv_robust(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        with pytest.raises(IngestionError, match="File not found"):
            load_csv_robust("/nonexistent/file.csv")


class TestDatasetManifest:
    """Tests for DatasetManifest dataclass."""

    def test_to_dict(self):
        manifest = DatasetManifest(
            name="test",
            source="test_source",
            url="https://example.com",
            local_path="/tmp/test.csv",
            checksum="abc123",
            status="validated"
        )
        d = manifest.to_dict()
        assert d['name'] == "test"
        assert d['status'] == "validated"
        assert d['checksum'] == "abc123"

    def test_from_dict(self):
        data = {
            'name': 'test',
            'source': 'test_source',
            'url': 'https://example.com',
            'local_path': '/tmp/test.csv',
            'checksum': 'abc123',
            'status': 'validated',
            'error_message': None,
            'file_size': 100,
            'download_timestamp': None
        }
        manifest = DatasetManifest.from_dict(data)
        assert manifest.name == "test"
        assert manifest.status == "validated"


class TestManifestIO:
    """Tests for manifest creation and loading."""

    def test_create_and_load_manifest(self):
        manifests = [
            DatasetManifest(
                name="test1",
                source="source1",
                url="https://example.com/1",
                local_path="/tmp/1.csv",
                status="validated"
            ),
            DatasetManifest(
                name="test2",
                source="source2",
                url="https://example.com/2",
                local_path="/tmp/2.csv",
                status="pending"
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            create_manifest(manifests, manifest_path)

            assert manifest_path.exists()

            loaded_manifests = load_manifest(manifest_path)
            assert len(loaded_manifests) == 2
            assert loaded_manifests[0].name == "test1"
            assert loaded_manifests[1].status == "pending"

    def test_load_nonexistent_manifest(self):
        with pytest.raises(IngestionError, match="Manifest file not found"):
            load_manifest("/nonexistent/manifest.json")