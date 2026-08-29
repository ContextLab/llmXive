import json
import tempfile
from pathlib import Path

import pytest

from code.data.checksum import (
    compute_sha256,
    generate_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
)


@pytest.fixture
def temp_dir_with_files(tmp_path: Path) -> Path:
    """Create a temporary directory with test files."""
    # Create subdirectories
    raw_dir = tmp_path / "raw"
    curated_dir = tmp_path / "curated"
    raw_dir.mkdir()
    curated_dir.mkdir()
    
    # Create test files
    file1 = raw_dir / "test1.txt"
    file1.write_text("Hello, World!")
    
    file2 = raw_dir / "test2.csv"
    file2.write_text("a,b,c\n1,2,3")
    
    file3 = curated_dir / "data.json"
    file3.write_text('{"key": "value"}')
    
    return tmp_path


def test_compute_sha256(temp_dir_with_files: Path) -> None:
    """Test SHA256 computation for a known file."""
    file_path = temp_dir_with_files / "raw" / "test1.txt"
    checksum = compute_sha256(file_path)
    
    # Known SHA256 for "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected


def test_generate_checksums(temp_dir_with_files: Path) -> None:
    """Test checksum generation for all files in a directory."""
    checksums = generate_checksums(temp_dir_with_files)
    
    assert len(checksums) == 3
    assert "raw/test1.txt" in checksums
    assert "raw/test2.csv" in checksums
    assert "curated/data.json" in checksums


def test_save_and_load_checksums(temp_dir_with_files: Path) -> None:
    """Test saving and loading checksums to/from JSON."""
    checksums = generate_checksums(temp_dir_with_files)
    
    output_path = temp_dir_with_files / "checksums.json"
    save_checksums(checksums, output_path)
    
    assert output_path.exists()
    
    loaded_checksums = load_checksums(output_path)
    assert loaded_checksums == checksums


def test_verify_checksums_success(temp_dir_with_files: Path) -> None:
    """Test successful checksum verification."""
    checksums = generate_checksums(temp_dir_with_files)
    failed = verify_checksums(checksums, temp_dir_with_files)
    
    assert len(failed) == 0


def test_verify_checksums_failure(temp_dir_with_files: Path) -> None:
    """Test checksum verification with corrupted files."""
    checksums = generate_checksums(temp_dir_with_files)
    
    # Corrupt a file
    file_path = temp_dir_with_files / "raw" / "test1.txt"
    file_path.write_text("Modified content")
    
    failed = verify_checksums(checksums, temp_dir_with_files)
    
    assert len(failed) == 1
    assert "raw/test1.txt" in failed


def test_verify_missing_file(temp_dir_with_files: Path) -> None:
    """Test checksum verification with missing files."""
    checksums = generate_checksums(temp_dir_with_files)
    
    # Remove a file
    file_path = temp_dir_with_files / "raw" / "test2.csv"
    file_path.unlink()
    
    failed = verify_checksums(checksums, temp_dir_with_files)
    
    assert len(failed) == 1
    assert "raw/test2.csv" in failed