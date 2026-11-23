"""
Legacy test file for hash utilities.
Kept for backward compatibility, delegates to code.tests.test_hash_unit.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    file_path = temp_dir / "sample.txt"
    content = "Hello, World! This is a test file for hashing."
    file_path.write_text(content)
    return file_path


def test_calculate_sha256(sample_file):
    content = sample_file.read_text()
    expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash


def test_calculate_sha256_nonexistent(temp_dir):
    missing_path = temp_dir / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        calculate_sha256(missing_path)


def test_calculate_sha256_directory(temp_dir):
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_dir)


def test_generate_manifest(sample_file, temp_dir):
    manifest = generate_manifest([sample_file])
    assert "artifacts" in manifest
    assert str(sample_file) in manifest["artifacts"]


def test_generate_manifest_writes_file(sample_file, temp_dir):
    output_path = temp_dir / "manifest.json"
    manifest = generate_manifest([sample_file], output_path)
    assert output_path.exists()


def test_verify_manifest_success(sample_file, temp_dir):
    output_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], output_path)
    assert verify_manifest(output_path) is True
