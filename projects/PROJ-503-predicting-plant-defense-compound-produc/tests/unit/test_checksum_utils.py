"""
Unit tests for checksum_utils.py
"""
import json
import tempfile
from pathlib import Path
import pytest

from checksum_utils import (
    calculate_sha256,
    validate_checksums,
    generate_checksums,
    main
)
from exceptions import E_DATASET


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        # Create test files
        (data_dir / "file1.txt").write_text("Hello, World!")
        (data_dir / "file2.txt").write_text("Test data for checksums")
        (data_dir / "file3.bin").write_bytes(b"\x00\x01\x02\x03")
        yield data_dir


@pytest.fixture
def checksums_manifest(temp_data_dir):
    """Create a valid checksum manifest."""
    manifest_path = temp_data_dir.parent / "checksums.json"
    checksums = {}
    for f in temp_data_dir.iterdir():
        checksums[f.name] = calculate_sha256(f)
    with open(manifest_path, "w") as mf:
        json.dump(checksums, mf)
    return manifest_path


def test_calculate_sha256(temp_data_dir):
    """Test SHA-256 calculation for a known string."""
    file_path = temp_data_dir / "file1.txt"
    hash_val = calculate_sha256(file_path)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in hash_val)


def test_calculate_sha256_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(Path("/nonexistent/file.txt"))


def test_validate_checksums_success(checksums_manifest, temp_data_dir):
    """Test successful validation of all files."""
    result = validate_checksums(checksums_manifest, temp_data_dir, expected_coverage=1.0)
    assert result["success"] is True
    assert len(result["passed"]) == 3
    assert len(result["failed"]) == 0
    assert len(result["missing"]) == 0
    assert result["coverage"] == 1.0


def test_validate_checksums_corrupted_file(checksums_manifest, temp_data_dir):
    """Test validation fails when a file is corrupted."""
    # Corrupt a file
    (temp_data_dir / "file1.txt").write_text("Corrupted content")

    result = validate_checksums(checksums_manifest, temp_data_dir, expected_coverage=0.6)
    assert result["success"] is False
    assert "file1.txt" in result["failed"]
    assert len(result["passed"]) == 2


def test_validate_checksums_missing_file(checksums_manifest, temp_data_dir):
    """Test validation handles missing files."""
    # Remove a file
    (temp_data_dir / "file2.txt").unlink()

    result = validate_checksums(checksums_manifest, temp_data_dir, expected_coverage=0.6)
    assert result["success"] is False
    assert "file2.txt" in result["missing"]
    assert len(result["passed"]) == 2


def test_validate_checksums_missing_manifest():
    """Test that missing manifest raises E_DATASET."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(E_DATASET):
            validate_checksums(Path(tmpdir) / "missing.json", Path(tmpdir))


def test_validate_checksums_invalid_manifest(temp_data_dir):
    """Test that invalid JSON manifest raises E_DATASET."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json")
        invalid_manifest = Path(f.name)

    try:
        with pytest.raises(E_DATASET):
            validate_checksums(invalid_manifest, temp_data_dir)
    finally:
        invalid_manifest.unlink()


def test_generate_checksums(temp_data_dir):
    """Test generation of checksums manifest."""
    output_path = temp_data_dir.parent / "generated_checksums.json"
    checksums = generate_checksums(temp_data_dir, output_path)

    assert output_path.exists()
    assert len(checksums) == 3
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert "file3.bin" in checksums

    # Verify content matches
    with open(output_path) as f:
        saved = json.load(f)
    assert saved == checksums


def test_generate_checksums_nonexistent_dir():
    """Test generation fails for non-existent directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            generate_checksums(Path(tmpdir) / "nonexistent", Path(tmpdir) / "out.json")