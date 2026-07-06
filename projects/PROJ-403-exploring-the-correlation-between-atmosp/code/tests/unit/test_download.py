import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import yaml

from src.data.download import calculate_sha256, verify_checksum, store_metadata
from src.utils.logger import setup_logging

# Setup logging for tests
setup_logging(level="DEBUG")


def test_calculate_sha256():
    """Test SHA256 calculation on a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello, World!")
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = calculate_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)


def test_verify_checksum_success():
    """Test successful checksum verification."""
    content = b"Test content for verification"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        correct_hash = hashlib.sha256(content).hexdigest()
        assert verify_checksum(tmp_path, correct_hash) is True
    finally:
        os.unlink(tmp_path)


def test_verify_checksum_failure():
    """Test checksum verification failure."""
    content = b"Test content"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        wrong_hash = hashlib.sha256(b"Wrong content").hexdigest()
        assert verify_checksum(tmp_path, wrong_hash) is False
    finally:
        os.unlink(tmp_path)


def test_store_metadata():
    """Test storing metadata to a YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        file1 = os.path.join(tmpdir, "file1.nc")
        file2 = os.path.join(tmpdir, "file2.nc")
        
        with open(file1, "wb") as f:
            f.write(b"data1")
        with open(file2, "wb") as f:
            f.write(b"data2")

        metadata_path = os.path.join(tmpdir, "metadata.yaml")
        
        store_metadata(
            file_paths=[file1, file2],
            metadata_path=metadata_path,
            data_source="Test Source"
        )

        assert os.path.exists(metadata_path)
        
        with open(metadata_path, "r") as f:
            data = yaml.safe_load(f)

        assert data["data_source"] == "Test Source"
        assert len(data["files"]) == 2
        
        filenames = {f["filename"] for f in data["files"]}
        assert "file1.nc" in filenames
        assert "file2.nc" in filenames
        
        # Verify hashes
        for file_entry in data["files"]:
            expected_hash = hashlib.sha256(
                b"data1" if file_entry["filename"] == "file1.nc" else b"data2"
            ).hexdigest()
            assert file_entry["sha256"] == expected_hash
            assert file_entry["size_bytes"] > 0
