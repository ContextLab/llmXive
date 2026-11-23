"""
Unit tests for the checksum utility.
"""

import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Add code directory to path for imports if running as standalone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.checksum import compute_file_checksum, generate_checksum_record, write_checksums_to_pending


def test_compute_file_checksum():
    """Test that compute_file_checksum returns the correct SHA-256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        # Compute expected hash manually
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_file_checksum(temp_path)

        assert actual_hash == expected_hash, f"Expected {expected_hash}, got {actual_hash}"
    finally:
        os.unlink(temp_path)


def test_generate_checksum_record():
    """Test that generate_checksum_record produces a valid dictionary."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test data")
        temp_path = Path(f.name)

    try:
        checksum = compute_file_checksum(temp_path)
        record = generate_checksum_record(temp_path, checksum)

        assert 'file_path' in record
        assert 'checksum' in record
        assert 'size_bytes' in record
        assert 'modified_at' in record
        assert 'created_at' in record

        assert record['checksum'] == checksum
        assert record['size_bytes'] == temp_path.stat().st_size
    finally:
        os.unlink(temp_path)


def test_write_checksums_to_pending(tmp_path):
    """Test that write_checksums_to_pending writes a valid YAML file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Data for checksum")

    checksum = compute_file_checksum(test_file)
    record = generate_checksum_record(test_file, checksum)

    pending_file = tmp_path / "pending" / "checksums.yaml"
    write_checksums_to_pending([record], pending_file)

    assert pending_file.exists()

    with open(pending_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    assert 'generated_at' in data
    assert 'checksums' in data
    assert len(data['checksums']) == 1
    assert data['checksums'][0]['checksum'] == checksum