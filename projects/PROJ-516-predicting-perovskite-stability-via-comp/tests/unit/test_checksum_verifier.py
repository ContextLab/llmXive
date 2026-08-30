"""
Unit tests for the Checksum Verifier module.
"""
import hashlib
import json
import tempfile
import os
from pathlib import Path
import pytest
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.checksum_verifier import (
    compute_sha256,
    validate_checksum,
    verify_artifacts_from_manifest,
    generate_checksum_manifest,
    ChecksumError
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        path = Path(f.name)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_compute_sha256(temp_file):
    """Test that compute_sha256 returns the correct hash."""
    # Calculate expected hash manually
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    result = compute_sha256(temp_file)
    assert result == expected


def test_compute_sha256_file_not_found():
    """Test that compute_sha256 raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))


def test_validate_checksum_valid(temp_file):
    """Test validation with correct checksum."""
    correct_hash = hashlib.sha256(b"Hello, World!").hexdigest()
    is_valid, computed = validate_checksum(temp_file, correct_hash)
    assert is_valid is True
    assert computed == correct_hash


def test_validate_checksum_invalid(temp_file):
    """Test validation with incorrect checksum."""
    wrong_hash = "a" * 64
    is_valid, computed = validate_checksum(temp_file, wrong_hash)
    assert is_valid is False
    assert computed == hashlib.sha256(b"Hello, World!").hexdigest()


def test_validate_checksum_missing_file():
    """Test validation raises ChecksumError for missing file."""
    with pytest.raises(ChecksumError):
        validate_checksum(Path("/nonexistent/file.txt"), "dummy_hash")


def test_validate_checksum_unsupported_algorithm(temp_file):
    """Test validation raises ChecksumError for unsupported algorithm."""
    with pytest.raises(ChecksumError):
        validate_checksum(temp_file, "dummy_hash", algorithm="md5")


def test_generate_checksum_manifest(temp_dir):
    """Test manifest generation."""
    # Create test files
    file1 = temp_dir / "file1.txt"
    file1.write_text("Content 1")
    file2 = temp_dir / "file2.txt"
    file2.write_text("Content 2")

    manifest_path = temp_dir / "manifest.yaml"
    generate_checksum_manifest(temp_dir, manifest_path)

    assert manifest_path.exists()

    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)

    assert "file1.txt" in manifest
    assert "file2.txt" in manifest
    assert len(manifest) == 2


def test_verify_artifacts_from_manifest_json(temp_dir):
    """Test artifact verification using JSON manifest."""
    # Create test file
    test_file = temp_dir / "data.csv"
    test_file.write_text("a,b,c\n1,2,3")
    expected_hash = hashlib.sha256(b"a,b,c\n1,2,3").hexdigest()

    # Create JSON manifest
    manifest_path = temp_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"data.csv": expected_hash}, f)

    results = verify_artifacts_from_manifest(manifest_path, temp_dir)
    assert results["data.csv"] is True


def test_verify_artifacts_from_manifest_yaml(temp_dir):
    """Test artifact verification using YAML manifest."""
    # Create test file
    test_file = temp_dir / "data.csv"
    test_file.write_text("a,b,c\n1,2,3")
    expected_hash = hashlib.sha256(b"a,b,c\n1,2,3").hexdigest()

    # Create YAML manifest
    manifest_path = temp_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump({"data.csv": expected_hash}, f)

    results = verify_artifacts_from_manifest(manifest_path, temp_dir)
    assert results["data.csv"] is True


def test_verify_artifacts_from_manifest_missing_file(temp_dir):
    """Test verification fails for missing artifact."""
    manifest_path = temp_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump({"missing.csv": "dummy_hash"}, f)

    results = verify_artifacts_from_manifest(manifest_path, temp_dir)
    assert results["missing.csv"] is False


def test_verify_artifacts_from_manifest_missing_manifest(temp_dir):
    """Test verification raises error if manifest missing."""
    with pytest.raises(FileNotFoundError):
        verify_artifacts_from_manifest(temp_dir / "nonexistent.yaml", temp_dir)
