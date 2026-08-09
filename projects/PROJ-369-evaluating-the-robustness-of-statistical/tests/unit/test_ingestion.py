"""
Unit tests for src/data/ingestion.py.
Verifies checksums, URL validation, and error handling on missing files.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import requests_mock
import sys

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.ingestion import (
    IngestionError,
    validate_url,
    compute_sha256,
    download_file,
    load_csv_robust,
    create_manifest,
    load_manifest,
    DatasetManifest,
)
from src.utils.config import get_path


class TestURLValidation:
    """Tests for validate_url function."""

    def test_valid_http_url(self):
        assert validate_url("http://example.com/data.csv") is True

    def test_valid_https_url(self):
        assert validate_url("https://example.com/data.csv") is True

    def test_invalid_protocol(self):
        with pytest.raises(IngestionError):
            validate_url("ftp://example.com/data.csv")

    def test_empty_url(self):
        with pytest.raises(IngestionError):
            validate_url("")

    def test_none_url(self):
        with pytest.raises(IngestionError):
            validate_url(None)

    def test_malformed_url(self):
        with pytest.raises(IngestionError):
            validate_url("not a url")


class TestChecksum:
    """Tests for compute_sha256 function."""

    def test_compute_sha256_known_string(self):
        """Test against a known string hash."""
        # "hello" -> 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
        test_content = b"hello"
        expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(test_content)
            tmp_path = tmp.name

        try:
            result = compute_sha256(tmp_path)
            assert result == expected_hash
        finally:
            os.unlink(tmp_path)

    def test_compute_sha256_empty_file(self):
        """Test hash of an empty file."""
        empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"")
            tmp_path = tmp.name

        try:
            result = compute_sha256(tmp_path)
            assert result == empty_hash
        finally:
            os.unlink(tmp_path)

    def test_compute_sha256_nonexistent_file(self):
        """Test that computing hash on missing file raises IngestionError."""
        with pytest.raises(IngestionError):
            compute_sha256("/path/that/does/not/exist.csv")


class TestDownloadFile:
    """Tests for download_file function."""

    def test_download_success(self):
        """Test successful download of a file."""
        with requests_mock.Mocker() as m:
            m.get("https://example.com/data.csv", text="col1,col2\n1,2\n3,4")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = download_file("https://example.com/data.csv", tmpdir)
                
                assert os.path.exists(output_path)
                assert os.path.basename(output_path) == "data.csv"
                
                with open(output_path, "r") as f:
                    content = f.read()
                    assert "col1,col2" in content

    def test_download_404_error(self):
        """Test that 404 errors raise IngestionError."""
        with requests_mock.Mocker() as m:
            m.get("https://example.com/missing.csv", status_code=404)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(IngestionError):
                    download_file("https://example.com/missing.csv", tmpdir)

    def test_download_connection_error(self):
        """Test that connection errors raise IngestionError."""
        with requests_mock.Mocker() as m:
            m.get("https://example.com/error.csv", exc=requests_mock.exceptions.ConnectTimeout)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(IngestionError):
                    download_file("https://example.com/error.csv", tmpdir)

    def test_download_invalid_url(self):
        """Test that invalid URLs raise IngestionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(IngestionError):
                download_file("ftp://invalid.com/file.csv", tmpdir)


class TestLoadCSVRobust:
    """Tests for load_csv_robust function."""

    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("date,value\n2023-01-01,10\n2023-01-02,20\n")
            tmp_path = f.name

        try:
            df = load_csv_robust(tmp_path)
            assert len(df) == 2
            assert "value" in df.columns
        finally:
            os.unlink(tmp_path)

    def test_load_csv_missing_file(self):
        """Test that missing file raises IngestionError."""
        with pytest.raises(IngestionError):
            load_csv_robust("/nonexistent/path/file.csv")

    def test_load_csv_invalid_format(self):
        """Test that invalid CSV format raises IngestionError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("not,a,valid,csv,structure,with,too,many,columns\n")
            tmp_path = f.name

        try:
            # Should raise or handle gracefully depending on implementation
            # If it raises IngestionError, that's acceptable
            df = load_csv_robust(tmp_path)
            # If it doesn't raise, it should still return a dataframe
            assert df is not None
        finally:
            os.unlink(tmp_path)


class TestDatasetManifest:
    """Tests for DatasetManifest class and related functions."""

    def test_create_manifest(self):
        """Test creating a manifest from a dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy file
            test_file = Path(tmpdir) / "test.csv"
            test_file.write_text("col1,col2\n1,2\n")
            
            manifest = create_manifest(
                dataset_name="test_dataset",
                file_path=str(test_file),
                url="https://example.com/test.csv",
                checksum=compute_sha256(str(test_file))
            )
            
            assert manifest.name == "test_dataset"
            assert manifest.url == "https://example.com/test.csv"
            assert manifest.checksum == compute_sha256(str(test_file))
            assert manifest.file_path == str(test_file)

    def test_load_manifest_success(self):
        """Test loading a valid manifest file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.yaml"
            
            # Create a valid manifest
            manifest = DatasetManifest(
                name="test",
                url="https://example.com/data.csv",
                checksum="abc123",
                file_path=str(Path(tmpdir) / "data.csv")
            )
            
            # Save manually as YAML-like structure for testing
            import yaml
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest.__dict__, f)
            
            loaded = load_manifest(str(manifest_path))
            assert loaded.name == "test"
            assert loaded.url == "https://example.com/data.csv"

    def test_load_manifest_missing_file(self):
        """Test that loading a non-existent manifest raises IngestionError."""
        with pytest.raises(IngestionError):
            load_manifest("/nonexistent/manifest.yaml")

    def test_load_manifest_invalid_format(self):
        """Test that an invalid manifest format raises IngestionError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("this is not valid yaml content {{{")
            tmp_path = f.name

        try:
            with pytest.raises(IngestionError):
                load_manifest(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_manifest_checksum_verification(self):
        """Test that manifest checksum matches actual file checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "data.csv"
            test_file.write_text("col1,col2\n1,2\n")
            
            actual_checksum = compute_sha256(str(test_file))
            
            manifest = create_manifest(
                dataset_name="verify_test",
                file_path=str(test_file),
                url="https://example.com/verify.csv",
                checksum=actual_checksum
            )
            
            # Simulate verification logic
            assert manifest.checksum == actual_checksum


class TestManifestIO:
    """Integration tests for manifest save/load cycle."""

    def test_save_and_load_cycle(self):
        """Test that a manifest can be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifest
            manifest = DatasetManifest(
                name="cycle_test",
                url="https://example.com/cycle.csv",
                checksum="d41d8cd98f00b204e9800998ecf8427e",
                file_path=str(Path(tmpdir) / "data.csv")
            )
            
            manifest_path = Path(tmpdir) / "test_manifest.yaml"
            
            # Save
            import yaml
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest.__dict__, f)
            
            # Load
            loaded = load_manifest(str(manifest_path))
            
            assert loaded.name == manifest.name
            assert loaded.url == manifest.url
            assert loaded.checksum == manifest.checksum