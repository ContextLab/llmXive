import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.utils.checksum import calculate_sha256, find_files, generate_checksums, verify_checksums

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        # Known hash for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = calculate_sha256(temp_path)
        assert result == expected, f"Expected {expected}, got {result}"
    finally:
        os.unlink(temp_path)

def test_find_files():
    """Test file finding logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Create nested structure
        (tmppath / "subdir").mkdir()
        (tmppath / "file1.txt").touch()
        (tmppath / "subdir" / "file2.txt").touch()
        (tmppath / "subdir" / "file3.log").touch()

        # Find all
        all_files = find_files(tmppath)
        assert len(all_files) == 3

        # Find only .txt
        txt_files = find_files(tmppath, extensions=[".txt"])
        assert len(txt_files) == 2
        assert all(f.suffix == ".txt" for f in txt_files)

def test_generate_checksums_integration(tmp_path):
    """Test full checksum generation flow."""
    # Create a mock directory structure similar to the project
    test_dirs = [
        tmp_path / "data" / "configs",
        tmp_path / "data" / "results",
        tmp_path / "state"
    ]
    for d in test_dirs:
        d.mkdir(parents=True)
        (d / "test.txt").write_text("test content")

    output_file = tmp_path / "checksums.json"
    
    # Run generation
    result = generate_checksums(output_file)
    
    # Verify output
    assert output_file.exists()
    assert "files" in result
    assert len(result["files"]) > 0
    
    # Verify JSON content
    with open(output_file) as f:
        data = json.load(f)
    assert "files" in data
    
def test_verify_checksums(tmp_path):
    """Test checksum verification."""
    # Setup
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    test_file = state_dir / "verify_test.txt"
    test_file.write_text("verify me")
    
    checksum_file = tmp_path / "checksums.json"
    
    # Generate initial
    generate_checksums(checksum_file)
    
    # Verify should pass
    assert verify_checksums(checksum_file) is True
    
    # Modify file
    test_file.write_text("modified")
    
    # Verify should fail
    assert verify_checksums(checksum_file) is False