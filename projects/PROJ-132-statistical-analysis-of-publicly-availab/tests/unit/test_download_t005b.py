"""
Unit tests for T005b: Download Verified eBird Sample
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import json
import hashlib

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.download_t005b import (
    compute_sha256,
    verify_checksums,
    write_success_report,
    run_download_pipeline,
)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_root = tempfile.mkdtemp()
    temp_output = Path(temp_root) / "output"
    temp_output.mkdir()
    temp_archive = Path(temp_root) / "archive"
    temp_archive.mkdir()
    yield {
        "root": Path(temp_root),
        "output": temp_output,
        "archive": temp_archive,
    }
    shutil.rmtree(temp_root)


def test_compute_sha256_basic(temp_dirs):
    """Test SHA-256 computation on a simple file."""
    test_file = temp_dirs["output"] / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(test_file)

    assert actual_hash == expected_hash


def test_compute_sha256_file_not_found(temp_dirs):
    """Test SHA-256 on non-existent file raises error."""
    non_existent = temp_dirs["output"] / "missing.txt"
    with pytest.raises(FileNotFoundError):
        compute_sha256(non_existent)


def test_verify_checksums_valid(temp_dirs):
    """Test checksum verification with valid data."""
    # Create test file
    test_file = temp_dirs["output"] / "test.parquet"
    content = b"test data"
    test_file.write_bytes(content)
    expected_hash = hashlib.sha256(content).hexdigest()

    # Create checksum file
    checksum_file = temp_dirs["output"] / "checksums.sha256"
    checksum_file.write_text(f"{expected_hash}  test.parquet\n")

    assert verify_checksums(checksum_file) is True


def test_verify_checksums_invalid(temp_dirs):
    """Test checksum verification with mismatched hash."""
    test_file = temp_dirs["output"] / "test.parquet"
    test_file.write_bytes(b"test data")

    checksum_file = temp_dirs["output"] / "checksums.sha256"
    checksum_file.write_text("wronghash  test.parquet\n")

    assert verify_checksums(checksum_file) is False


def test_verify_checksums_missing_file(temp_dirs):
    """Test checksum verification when file is missing."""
    checksum_file = temp_dirs["output"] / "checksums.sha256"
    checksum_file.write_text("somehash  missing.parquet\n")

    assert verify_checksums(checksum_file) is False


def test_write_success_report(temp_dirs):
    """Test writing a success report."""
    report_path = write_success_report(
        temp_dirs["output"], total_chunks=5, total_rows=500000
    )

    assert report_path.exists()
    with open(report_path) as f:
        report = json.load(f)

    assert report["status"] == "success"
    assert report["total_chunks"] == 5
    assert report["total_rows"] == 500000
    assert "output_dir" in report
    assert "checksum_file" in report


# Note: The full pipeline test (test_run_download_pipeline) is skipped
# because it requires actual network access to the HuggingFace dataset.
# In CI, this test would be run against the real dataset or mocked
# appropriately. For now, we verify the unit functions above.
def test_run_download_pipeline_skipped():
    """
    Skip full pipeline test in unit tests.
    This test requires real network access and large data download.
    """
    pytest.skip("Full pipeline test requires real dataset download.")