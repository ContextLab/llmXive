"""Tests for the checksum utility.

The test suite creates a temporary directory with a few small files,
generates a checksum file, mutates one file, and then verifies that the
verification logic correctly detects the mismatch.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.checksums import (
    compute_sha256,
    generate_checksums,
    write_checksums_file,
    load_checksums,
    verify_checksums,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def create_file(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(content)


def test_compute_sha256():
    data = b"llmXive checksum test"
    path = Path("tmpfile")
    create_file(path, data)
    expected = hashlib.sha256(data).hexdigest()
    assert compute_sha256(path) == expected
    path.unlink()


def test_generate_and_verify_checksums(temp_dir: Path):
    # Create a few files
    create_file(temp_dir / "a.txt", b"alpha")
    create_file(temp_dir / "sub" / "b.txt", b"beta")
    create_file(temp_dir / "c.bin", b"\x00\x01\x02")

    # Generate checksums
    checksums = generate_checksums(temp_dir)
    checksum_path = temp_dir / "checksums.json"
    write_checksums_file(checksums, checksum_path)

    # Load and compare – should succeed
    loaded = load_checksums(checksum_path)
    assert loaded == checksums
    assert verify_checksums(temp_dir, checksum_path) is True

    # Corrupt a file and verify detection
    (temp_dir / "a.txt").write_bytes(b"corrupted")
    assert verify_checksums(temp_dir, checksum_path) is False


def test_missing_checksums_file(temp_dir: Path, capsys):
    # No checksums.json present
    result = verify_checksums(temp_dir, temp_dir / "nonexistent.json")
    captured = capsys.readouterr()
    assert not result
    assert "Checksums file missing" in captured.out