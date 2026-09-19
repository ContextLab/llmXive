"""
Tests for checksum utilities in code/utils.py.
"""
import os
import tempfile
from pathlib import Path
import hashlib

import pytest

from utils import compute_sha256, verify_checksum, scan_directory_for_checksums, update_state_file_with_checksums


def test_compute_sha256_valid_file():
    """Test computing SHA-256 on a valid file."""
    content = b"Hello, world!"
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = compute_sha256(tmp_path)
        assert result == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_file_not_found():
    """Test that compute_sha256 raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))


def test_compute_sha256_directory():
    """Test that compute_sha256 raises IsADirectoryError for directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            compute_sha256(Path(tmpdir))


def test_verify_checksum_match():
    """Test verify_checksum returns True for matching checksums."""
    content = b"Test data"
    checksum = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        assert verify_checksum(tmp_path, checksum) is True
    finally:
        os.unlink(tmp_path)


def test_verify_checksum_mismatch():
    """Test verify_checksum returns False for mismatched checksums."""
    content = b"Test data"

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        assert verify_checksum(tmp_path, "0" * 64) is False
    finally:
        os.unlink(tmp_path)


def test_scan_directory_for_checksums():
    """Test scanning a directory for checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")

        # Scan with specific extension
        checksums = scan_directory_for_checksums(tmp_path, extensions=[".txt"])

        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert "subdir/file3.txt" in checksums

        # Verify checksums are correct
        for rel_path, cs in checksums.items():
            file_path = tmp_path / rel_path
            expected = hashlib.sha256(file_path.read_bytes()).hexdigest()
            assert cs == expected


def test_update_state_file_with_checksums():
    """Test updating the state file with checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        checksums = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }

        update_state_file_with_checksums(state_file, checksums, "raw")

        assert state_file.exists()
        import yaml
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)

        assert 'data_checksums' in data
        assert 'raw' in data['data_checksums']
        assert data['data_checksums']['raw']['files'] == checksums
        assert 'updated_at' in data['data_checksums']['raw']