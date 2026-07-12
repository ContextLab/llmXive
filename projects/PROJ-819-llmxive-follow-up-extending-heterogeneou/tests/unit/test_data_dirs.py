import os
import json
import tempfile
from pathlib import Path
import pytest

from setup_data_dirs import ensure_directories, calculate_sha256, generate_checksums, save_checksums

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_ensure_directories_creates_structure(temp_project_root):
    """Test that ensure_directories creates raw, derived, and hashes directories."""
    ensure_directories(temp_project_root)
    
    assert (temp_project_root / "data" / "raw").exists()
    assert (temp_project_root / "data" / "derived").exists()
    assert (temp_project_root / "state" / "hashes").exists()

def test_calculate_sha256_correct(temp_project_root):
    """Test that calculate_sha256 returns correct hash for a known file."""
    test_file = temp_project_root / "data" / "raw" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Hello, World!")
    
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    actual_hash = calculate_sha256(test_file)
    
    assert actual_hash == expected_hash

def test_generate_checksums(temp_project_root):
    """Test that generate_checksums finds and hashes files in data directories."""
    ensure_directories(temp_project_root)
    
    # Create a test file
    test_file = temp_project_root / "data" / "derived" / "sample.json"
    test_file.write_text('{"key": "value"}')
    
    checksums = generate_checksums(temp_project_root)
    
    assert len(checksums) == 1
    assert "data/derived/sample.json" in checksums
    assert checksums["data/derived/sample.json"] != ""

def test_save_and_load_checksums(temp_project_root):
    """Test that checksums can be saved and reloaded correctly."""
    ensure_directories(temp_project_root)
    
    # Create a test file
    test_file = temp_project_root / "data" / "raw" / "data.csv"
    test_file.write_text("col1,col2\n1,2")
    
    checksums = generate_checksums(temp_project_root)
    save_checksums(temp_project_root, checksums)
    
    checksum_file = temp_project_root / "state" / "hashes" / "checksums.json"
    assert checksum_file.exists()
    
    with open(checksum_file, "r") as f:
        loaded_checksums = json.load(f)
    
    assert loaded_checksums == checksums
