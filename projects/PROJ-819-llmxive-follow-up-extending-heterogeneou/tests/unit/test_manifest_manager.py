import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from reproducibility.manifest_manager import (
    calculate_sha256,
    ensure_directories,
    get_files_to_hash,
    generate_manifest,
    save_manifest,
    verify_manifest,
    main
)

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "raw").mkdir()
    (tmp_path / "data" / "derived").mkdir()
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "cache").mkdir()
    (tmp_path / "state").mkdir()
    
    # Create some test files
    (tmp_path / "data" / "raw" / "test.txt").write_text("test content")
    (tmp_path / "data" / "derived" / "output.json").write_text('{"key": "value"}')
    (tmp_path / "code" / "cache" / "module.py").write_text("print('hello')")
    
    return tmp_path

def test_calculate_sha256(temp_project_dir):
    """Test SHA-256 calculation."""
    file_path = temp_project_dir / "data" / "raw" / "test.txt"
    hash1 = calculate_sha256(file_path)
    hash2 = calculate_sha256(file_path)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex string length

def test_ensure_directories(temp_project_dir):
    """Test directory creation."""
    ensure_directories(temp_project_dir)
    assert (temp_project_dir / "state" / "hashes").exists()

def test_get_files_to_hash(temp_project_dir):
    """Test file discovery."""
    files = get_files_to_hash(temp_project_dir, ["data", "code"])
    assert len(files) == 3
    assert any("test.txt" in str(f) for f in files)
    assert any("output.json" in str(f) for f in files)
    assert any("module.py" in str(f) for f in files)

def test_generate_manifest(temp_project_dir):
    """Test manifest generation."""
    files = get_files_to_hash(temp_project_dir, ["data", "code"])
    manifest = generate_manifest(files, temp_project_dir)
    
    assert "files" in manifest
    assert len(manifest["files"]) == 3
    for file_entry in manifest["files"]:
        assert "path" in file_entry
        assert "sha256" in file_entry
        assert len(file_entry["sha256"]) == 64

def test_save_and_load_manifest(temp_project_dir):
    """Test saving and loading manifest."""
    files = get_files_to_hash(temp_project_dir, ["data", "code"])
    manifest = generate_manifest(files, temp_project_dir)
    
    manifest_path = temp_project_dir / "state" / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        loaded_manifest = json.load(f)
    
    assert loaded_manifest == manifest

def test_verify_manifest_valid(temp_project_dir):
    """Test manifest verification with valid files."""
    files = get_files_to_hash(temp_project_dir, ["data", "code"])
    manifest = generate_manifest(files, temp_project_dir)
    
    manifest_path = temp_project_dir / "state" / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    assert verify_manifest(manifest_path, temp_project_dir)

def test_verify_manifest_invalid_content(temp_project_dir):
    """Test manifest verification with modified content."""
    files = get_files_to_hash(temp_project_dir, ["data", "code"])
    manifest = generate_manifest(files, temp_project_dir)
    
    manifest_path = temp_project_dir / "state" / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    # Modify a file
    (temp_project_dir / "data" / "raw" / "test.txt").write_text("modified content")
    
    assert not verify_manifest(manifest_path, temp_project_dir)

def test_verify_manifest_missing_file(temp_project_dir):
    """Test manifest verification with missing file."""
    files = get_files_to_hash(temp_project_dir, ["data", "code"])
    manifest = generate_manifest(files, temp_project_dir)
    
    manifest_path = temp_project_dir / "state" / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    # Delete a file
    (temp_project_dir / "data" / "raw" / "test.txt").unlink()
    
    assert not verify_manifest(manifest_path, temp_project_dir)

def test_main_function(temp_project_dir, capsys):
    """Test the main function."""
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_dir)
        main()
        captured = capsys.readouterr()
        assert "Manifest generated" in captured.out
        assert "state/manifest.json" in captured.out
        
        # Verify manifest was created
        manifest_path = temp_project_dir / "state" / "manifest.json"
        assert manifest_path.exists()
    finally:
        os.chdir(original_cwd)