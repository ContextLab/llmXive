import json
import tempfile
from pathlib import Path

import pytest

from code.utils.checksum import (
    compute_file_checksum,
    generate_checksums_for_directory,
    save_checksums,
    load_checksums,
    verify_checksums,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)

        # Create subdirectories
        (base / "subdir").mkdir()

        # Create test files
        (base / "file1.txt").write_text("Hello, World!")
        (base / "file2.json").write_text('{"key": "value"}')
        (base / "subdir" / "file3.csv").write_text("a,b,c\n1,2,3")

        yield base


def test_compute_file_checksum(temp_dir):
    """Test checksum computation for a single file."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_checksum(file_path)

    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length

    # Verify consistency
    checksum2 = compute_file_checksum(file_path)
    assert checksum == checksum2

def test_compute_file_checksum_nonexistent():
    """Test that computing checksum for non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))

def test_compute_file_checksum_different_algorithms(temp_dir):
    """Test checksum computation with different algorithms."""
    file_path = temp_dir / "file1.txt"

    sha256_checksum = compute_file_checksum(file_path, algorithm="sha256")
    md5_checksum = compute_file_checksum(file_path, algorithm="md5")

    assert len(sha256_checksum) == 64
    assert len(md5_checksum) == 32
    assert sha256_checksum != md5_checksum

def test_generate_checksums_for_directory(temp_dir):
    """Test generating checksums for all files in a directory."""
    checksums = generate_checksums_for_directory(temp_dir, recursive=True)

    assert "file1.txt" in checksums
    assert "file2.json" in checksums
    assert "subdir/file3.csv" in checksums
    assert len(checksums) == 3

def test_generate_checksums_non_recursive(temp_dir):
    """Test generating checksums without recursion."""
    checksums = generate_checksums_for_directory(temp_dir, recursive=False)

    assert "file1.txt" in checksums
    assert "file2.json" in checksums
    assert "subdir" not in str(checksums.keys())  # No subdir files
    assert len(checksums) == 2

def test_generate_checksums_with_extension_filter(temp_dir):
    """Test generating checksums with extension filter."""
    checksums = generate_checksums_for_directory(temp_dir, extensions=[".txt"])

    assert "file1.txt" in checksums
    assert "file2.json" not in checksums
    assert "subdir/file3.csv" not in checksums
    assert len(checksums) == 1

def test_generate_checksums_not_a_directory():
    """Test that generating checksums for a file raises error."""
    with pytest.raises(NotADirectoryError):
        generate_checksums_for_directory(Path("file.txt"))

def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums from a manifest file."""
    with tempfile.TemporaryDirectory() as tmp_out:
        output_path = Path(tmp_out) / "checksums.json"
        checksums = generate_checksums_for_directory(temp_dir)

        save_checksums(checksums, output_path)

        assert output_path.exists()

        # Load and verify
        loaded_algorithm, loaded_checksums = load_checksums(output_path)

        assert loaded_algorithm == "sha256"
        assert loaded_checksums == checksums

def test_load_checksums_invalid_manifest():
    """Test loading an invalid manifest file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        invalid_path = Path(tmp_dir) / "invalid.json"
        invalid_path.write_text('{"invalid": "format"}')

        with pytest.raises(ValueError, match="missing 'checksums'"):
            load_checksums(invalid_path)

def test_verify_checksums_success(temp_dir):
    """Test successful checksum verification."""
    with tempfile.TemporaryDirectory() as tmp_out:
        manifest_path = Path(tmp_out) / "checksums.json"
        checksums = generate_checksums_for_directory(temp_dir)
        save_checksums(checksums, manifest_path)

        all_valid, missing, mismatched = verify_checksums(temp_dir, manifest_path)

        assert all_valid is True
        assert len(missing) == 0
        assert len(mismatched) == 0

def test_verify_checksums_missing_file(temp_dir):
    """Test verification with a missing file."""
    with tempfile.TemporaryDirectory() as tmp_out:
        manifest_path = Path(tmp_out) / "checksums.json"
        checksums = generate_checksums_for_directory(temp_dir)
        save_checksums(checksums, manifest_path)

        # Delete a file
        (temp_dir / "file1.txt").unlink()

        all_valid, missing, mismatched = verify_checksums(temp_dir, manifest_path)

        assert all_valid is False
        assert "file1.txt" in missing
        assert len(mismatched) == 0

def test_verify_checksums_mismatched_content(temp_dir):
    """Test verification with modified file content."""
    with tempfile.TemporaryDirectory() as tmp_out:
        manifest_path = Path(tmp_out) / "checksums.json"
        checksums = generate_checksums_for_directory(temp_dir)
        save_checksums(checksums, manifest_path)

        # Modify a file
        (temp_dir / "file1.txt").write_text("Modified content")

        all_valid, missing, mismatched = verify_checksums(temp_dir, manifest_path)

        assert all_valid is False
        assert len(missing) == 0
        assert "file1.txt" in mismatched

def test_verify_checksums_strict_mode(temp_dir):
    """Test that strict mode raises an error on verification failure."""
    with tempfile.TemporaryDirectory() as tmp_out:
        manifest_path = Path(tmp_out) / "checksums.json"
        checksums = generate_checksums_for_directory(temp_dir)
        save_checksums(checksums, manifest_path)

        # Modify a file
        (temp_dir / "file1.txt").write_text("Modified content")

        with pytest.raises(ValueError, match="Checksum verification failed"):
            verify_checksums(temp_dir, manifest_path, strict=True)

def test_verify_checksums_non_strict_mode(temp_dir):
    """Test that non-strict mode returns errors without raising."""
    with tempfile.TemporaryDirectory() as tmp_out:
        manifest_path = Path(tmp_out) / "checksums.json"
        checksums = generate_checksums_for_directory(temp_dir)
        save_checksums(checksums, manifest_path)

        # Modify a file
        (temp_dir / "file1.txt").write_text("Modified content")

        all_valid, missing, mismatched = verify_checksums(temp_dir, manifest_path, strict=False)

        assert all_valid is False
        assert len(mismatched) == 1