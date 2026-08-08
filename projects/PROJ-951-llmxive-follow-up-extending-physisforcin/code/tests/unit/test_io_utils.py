import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.io_utils import (
    ensure_dirs,
    calculate_file_checksum,
    calculate_directory_checksums,
    save_checksums,
    load_checksums,
    verify_directory_integrity,
    update_checksums,
    get_file_size,
    get_total_size,
    cleanup_empty_dirs,
    move_files_with_checksums,
    validate_project_structure,
    get_data_stats
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def populated_dir(temp_data_dir):
    """Create a directory with some test files."""
    (temp_data_dir / "subdir").mkdir()
    (temp_data_dir / "file1.txt").write_text("content1")
    (temp_data_dir / "subdir" / "file2.txt").write_text("content2")
    yield temp_data_dir

def test_ensure_dirs(temp_data_dir):
    new_dir = temp_data_dir / "new" / "nested" / "dir"
    ensure_dirs([new_dir])
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_ensure_dirs_existing(temp_data_dir):
    ensure_dirs([temp_data_dir])
    assert temp_data_dir.exists()

def test_calculate_file_checksum(temp_data_dir):
    test_file = temp_data_dir / "test.txt"
    test_file.write_text("hello world")
    checksum = calculate_file_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_calculate_file_checksum_nonexistent(temp_data_dir):
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(temp_data_dir / "nonexistent.txt")

def test_calculate_directory_checksums(temp_data_dir):
    (temp_data_dir / "a.txt").write_text("a")
    (temp_data_dir / "b.txt").write_text("b")
    checksums = calculate_directory_checksums(temp_data_dir)
    assert "a.txt" in checksums
    assert "b.txt" in checksums
    assert len(checksums) == 2

def test_save_and_load_checksums(temp_data_dir):
    test_file = temp_data_dir / "test.txt"
    test_file.write_text("test data")
    checksums = {"test.txt": calculate_file_checksum(test_file)}
    output_path = temp_data_dir / "checksums.json"
    save_checksums(checksums, output_path)
    
    loaded = load_checksums(output_path)
    assert loaded == checksums

def test_verify_directory_integrity(populated_dir):
    checksum_file = populated_dir / "checksums.json"
    update_checksums(populated_dir, checksum_file)
    
    # Verify unchanged
    loaded = load_checksums(checksum_file)
    valid, errors = verify_directory_integrity(populated_dir, loaded)
    assert valid
    assert len(errors) == 0

def test_verify_directory_integrity_modified(populated_dir):
    checksum_file = populated_dir / "checksums.json"
    update_checksums(populated_dir, checksum_file)
    
    # Modify a file
    (populated_dir / "file1.txt").write_text("modified content")
    
    loaded = load_checksums(checksum_file)
    valid, errors = verify_directory_integrity(populated_dir, loaded)
    assert not valid
    assert any("Corrupted" in err for err in errors)

def test_verify_directory_integrity_missing(populated_dir):
    checksum_file = populated_dir / "checksums.json"
    update_checksums(populated_dir, checksum_file)
    
    # Delete a file
    (populated_dir / "file1.txt").unlink()
    
    loaded = load_checksums(checksum_file)
    valid, errors = verify_directory_integrity(populated_dir, loaded)
    assert not valid
    assert any("Missing" in err for err in errors)

def test_update_checksums(temp_data_dir):
    (temp_data_dir / "new.txt").write_text("new")
    checksum_file = temp_data_dir / "checksums.json"
    update_checksums(temp_data_dir, checksum_file)
    assert checksum_file.exists()
    loaded = load_checksums(checksum_file)
    assert "new.txt" in loaded

def test_get_file_size(temp_data_dir):
    test_file = temp_data_dir / "size_test.txt"
    test_file.write_text("12345")
    size = get_file_size(test_file)
    assert size == 5

def test_get_total_size(temp_data_dir):
    (temp_data_dir / "a.txt").write_text("12345") # 5 bytes
    (temp_data_dir / "b.txt").write_text("123")   # 3 bytes
    total = get_total_size(temp_data_dir)
    assert total == 8

def test_cleanup_empty_dirs(temp_data_dir):
    (temp_data_dir / "empty1").mkdir()
    (temp_data_dir / "empty2").mkdir()
    (temp_data_dir / "non_empty").mkdir()
    (temp_data_dir / "non_empty" / "file.txt").write_text("x")
    
    count = cleanup_empty_dirs(temp_data_dir)
    assert count == 2
    assert not (temp_data_dir / "empty1").exists()
    assert (temp_data_dir / "non_empty").exists()

def test_move_files_with_checksums(temp_data_dir):
    src_dir = temp_data_dir / "src"
    dst_dir = temp_data_dir / "dst"
    src_dir.mkdir()
    
    (src_dir / "file.txt").write_text("content")
    checksum_file = temp_data_dir / "checksums.json"
    
    move_files_with_checksums(src_dir, dst_dir, ["file.txt"], checksum_file)
    
    assert not (src_dir / "file.txt").exists()
    assert (dst_dir / "file.txt").exists()
    assert checksum_file.exists()

def test_validate_project_structure(temp_data_dir):
    (temp_data_dir / "valid").mkdir()
    valid, missing = validate_project_structure(temp_data_dir, ["valid", "missing"])
    assert not valid
    assert "missing" in missing

def test_get_data_stats(temp_data_dir):
    (temp_data_dir / "data1").mkdir()
    (temp_data_dir / "data1" / "f.txt").write_text("x")
    
    stats = get_data_stats(temp_data_dir, ["data1", "missing"])
    assert "data1" in stats
    assert stats["data1"]["file_count"] == 1
    assert "error" in stats["missing"]
