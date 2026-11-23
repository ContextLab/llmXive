import os
import sys
import tempfile
import json
from pathlib import Path
import pytest
import logging

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_data_dirs import create_gitkeep, setup_data_directories, generate_checksums, verify_checksums

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        # Create the expected structure
        (root / "data").mkdir()
        (root / "code").mkdir()
        yield root

def test_create_gitkeep(temp_project_root):
    """Test that .gitkeep is created in a directory."""
    test_dir = temp_project_root / "data" / "raw"
    test_dir.mkdir()
    
    create_gitkeep(test_dir)
    
    assert (test_dir / ".gitkeep").exists()

def test_create_gitkeep_skips_existing(temp_project_root):
    """Test that .gitkeep is not recreated if it exists."""
    test_dir = temp_project_root / "data" / "raw"
    test_dir.mkdir()
    gitkeep = test_dir / ".gitkeep"
    gitkeep.write_text("existing content")
    
    create_gitkeep(test_dir)
    
    assert gitkeep.exists()
    assert gitkeep.read_text() == "existing content"

def test_setup_data_directories(temp_project_root):
    """Test that all required directories are created with .gitkeep files."""
    setup_data_directories(temp_project_root)
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/logs",
        "data/figures"
    ]
    
    for dir_path in required_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} was not created"
        assert (full_path / ".gitkeep").exists(), f".gitkeep missing in {dir_path}"

def test_generate_checksums_empty(temp_project_root):
    """Test checksum generation on empty directories."""
    setup_data_directories(temp_project_root)
    output_path = temp_project_root / "data" / "checksums.json"
    
    generate_checksums(temp_project_root / "data", output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    # Should be empty or only contain .gitkeep if logic included it (current logic excludes it)
    assert len(data) == 0

def test_generate_checksums_with_files(temp_project_root):
    """Test checksum generation with actual files."""
    setup_data_directories(temp_project_root)
    
    # Create a test file
    test_file = temp_project_root / "data" / "raw" / "test.txt"
    test_file.write_text("test content")
    
    output_path = temp_project_root / "data" / "checksums.json"
    generate_checksums(temp_project_root / "data", output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    
    assert "raw/test.txt" in data
    assert len(data["raw/test.txt"]) == 64  # SHA-256 hex length

def test_verify_checksums_success(temp_project_root):
    """Test checksum verification when files match."""
    setup_data_directories(temp_project_root)
    
    test_file = temp_project_root / "data" / "raw" / "test.txt"
    test_file.write_text("test content")
    
    output_path = temp_project_root / "data" / "checksums.json"
    generate_checksums(temp_project_root / "data", output_path)
    
    assert verify_checksums(temp_project_root / "data", output_path) is True

def test_verify_checksums_failure(temp_project_root):
    """Test checksum verification when files are modified."""
    setup_data_directories(temp_project_root)
    
    test_file = temp_project_root / "data" / "raw" / "test.txt"
    test_file.write_text("test content")
    
    output_path = temp_project_root / "data" / "checksums.json"
    generate_checksums(temp_project_root / "data", output_path)
    
    # Modify file
    test_file.write_text("modified content")
    
    assert verify_checksums(temp_project_root / "data", output_path) is False

def test_verify_checksums_missing_file(temp_project_root):
    """Test checksum verification when a file is missing."""
    setup_data_directories(temp_project_root)
    
    test_file = temp_project_root / "data" / "raw" / "test.txt"
    test_file.write_text("test content")
    
    output_path = temp_project_root / "data" / "checksums.json"
    generate_checksums(temp_project_root / "data", output_path)
    
    # Remove file
    test_file.unlink()
    
    assert verify_checksums(temp_project_root / "data", output_path) is False