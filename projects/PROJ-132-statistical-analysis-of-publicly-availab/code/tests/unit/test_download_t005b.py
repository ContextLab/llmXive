"""
Unit tests for T005b: Download Verified eBird Sample.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import json
import hashlib

# Add code directory to path if needed
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.data.download_t005b import compute_sha256, verify_checksums, write_success_report


class TestDownloadT005b:
    """Test cases for download_t005b module."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_base = tempfile.mkdtemp()
        data_raw = Path(temp_base) / "data" / "raw" / "ebird_sample"
        data_raw.mkdir(parents=True)
        yield data_raw
        shutil.rmtree(temp_base)

    def test_compute_sha256_basic(self, temp_dirs):
        """Test basic SHA-256 computation."""
        test_file = temp_dirs / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_compute_sha256_empty_file(self, temp_dirs):
        """Test SHA-256 on empty file."""
        test_file = temp_dirs / "empty.txt"
        test_file.write_bytes(b"")

        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_verify_checksums_creates_file(self, temp_dirs):
        """Test that verify_checksums creates the checksums file."""
        # Create dummy files
        (temp_dirs / "file1.jsonl").write_text("{}")
        (temp_dirs / "file2.jsonl").write_text("{}")

        checksums_file = temp_dirs / "checksums.json"
        result = verify_checksums(temp_dirs, checksums_file)

        assert result is True
        assert checksums_file.exists()

        # Verify JSON structure
        with open(checksums_file) as f:
            checksums = json.load(f)

        assert "file1.jsonl" in checksums
        assert "file2.jsonl" in checksums
        assert all(len(h) == 64 for h in checksums.values())  # SHA-256 hex length

    def test_write_success_report(self, temp_dirs):
        """Test writing success report."""
        report_file = temp_dirs / "success_report.json"
        checksums_file = temp_dirs / "checksums.json"
        checksums_file.write_text("{}")

        write_success_report(temp_dirs, report_file, checksums_file)

        assert report_file.exists()

        with open(report_file) as f:
            report = json.load(f)

        assert report["task_id"] == "T005b"
        assert report["status"] == "success"
        assert "files" in report