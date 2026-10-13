"""
Unit tests for checksum utilities (T002).

Verification: pytest tests/unit/test_checksum.py exits 0 and the
test asserts the correct SHA-256 of a known file.
"""
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.checksum import (
    calculate_checksum,
    generate_checksum_manifest,
    load_checksum_manifest,
    sha256_file,
    verify_checksum,
)

# Known SHA-256 test vectors (FIPS 180-2 / well-known values).
KNOWN_VECTORS = {
    b"abc": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    b"": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}


@pytest.fixture
def known_file():
    """Create a temporary file with known content 'abc'."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write(b"abc")
        path = f.name
    yield path
    os.unlink(path)


def test_sha256_file_known_vector(known_file):
    """sha256_file returns the correct SHA-256 of a known file."""
    assert sha256_file(known_file) == KNOWN_VECTORS[b"abc"]


def test_sha256_file_empty_file():
    """sha256_file of an empty file equals the empty-string digest."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        path = f.name
    try:
        assert sha256_file(path) == KNOWN_VECTORS[b""]
    finally:
        os.unlink(path)


def test_sha256_file_matches_hashlib(known_file):
    """sha256_file agrees with hashlib on arbitrary content."""
    content = b"pull request diff sample \x00\x01 payload"
    with open(known_file, "wb") as f:
        f.write(content)
    assert sha256_file(known_file) == hashlib.sha256(content).hexdigest()


def test_sha256_file_accepts_str_and_path(known_file):
    """sha256_file works with both str and Path inputs."""
    assert sha256_file(known_file) == sha256_file(Path(known_file))


def test_sha256_file_returns_hex_string(known_file):
    checksum = sha256_file(known_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)


def test_sha256_file_deterministic(known_file):
    assert sha256_file(known_file) == sha256_file(known_file)


def test_sha256_file_missing_raises():
    with pytest.raises(FileNotFoundError):
        sha256_file("/nonexistent/path/file.json")


def test_sha256_file_directory_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            sha256_file(tmpdir)


def test_sha256_file_large_file_chunked():
    """Files larger than the read chunk are hashed correctly."""
    content = os.urandom(200_000)
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        assert sha256_file(path) == hashlib.sha256(content).hexdigest()
    finally:
        os.unlink(path)


def test_calculate_checksum_alias(known_file):
    """calculate_checksum is an alias of sha256_file."""
    assert calculate_checksum(known_file) == sha256_file(known_file)


def test_verify_checksum_matches(known_file):
    expected = KNOWN_VECTORS[b"abc"]
    assert verify_checksum(known_file, expected) is True


def test_verify_checksum_case_insensitive(known_file):
    assert verify_checksum(known_file, KNOWN_VECTORS[b"abc"].upper()) is True


def test_verify_checksum_mismatch(known_file):
    assert verify_checksum(known_file, "a" * 64) is False


def test_verify_checksum_invalid_format(known_file):
    with pytest.raises(ValueError):
        verify_checksum(known_file, "invalid")


def test_manifest_roundtrip(known_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        generate_checksum_manifest([known_file], manifest_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest == {Path(known_file).name: KNOWN_VECTORS[b"abc"]}
        loaded = load_checksum_manifest(manifest_path)
        assert loaded == manifest


def test_manifest_skips_missing_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        generate_checksum_manifest(["/nonexistent/file.json"], manifest_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            assert json.load(f) == {}
