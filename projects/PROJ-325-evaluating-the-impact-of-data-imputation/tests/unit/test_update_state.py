"""
Tests for update_state module.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
import hashlib

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from update_state import compute_file_hash, find_artifacts, generate_manifest, update_manifest

def test_compute_file_hash():
    """Test that compute_file_hash returns correct SHA-256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        # Compute expected hash manually
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        
        # Compute using function
        actual_hash = compute_file_hash(temp_path)
        
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_compute_file_hash_nonexistent():
    """Test that compute_file_hash raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("/nonexistent/file.txt"))

def test_find_artifacts():
    """Test that find_artifacts correctly identifies files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.csv").touch()
        (tmp_path / "file3.txt").touch()
        (tmp_path / "ignored.json").touch()  # This should be ignored
        
        # Create subdirectory with file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.yaml").touch()
        
        # Create hidden file (should be ignored)
        (tmp_path / ".hidden").touch()
        
        results = find_artifacts(tmp_path)
        
        # Check that expected files are found
        result_names = [p.name for p in results]
        assert "file1.py" in result_names
        assert "file2.csv" in result_names
        assert "file3.txt" in result_names
        assert "nested.yaml" in result_names
        
        # Check that ignored files are not found
        assert "ignored.json" not in result_names
        assert ".hidden" not in result_names

def test_find_artifacts_nonexistent_dir():
    """Test that find_artifacts returns empty list for non-existent directory."""
    results = find_artifacts(Path("/nonexistent/directory"))
    assert results == []

def test_generate_manifest():
    """Test that generate_manifest creates correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Mock PROJECT_ROOT temporarily
        import update_state
        original_root = update_state.PROJECT_ROOT
        update_state.PROJECT_ROOT = tmp_path
        
        try:
            manifest = generate_manifest(["."])
            
            assert "artifact_hashes" in manifest
            assert "version" in manifest
            assert "updated_at" in manifest
            
            # Check that our test file is in the manifest
            assert "test.txt" in manifest["artifact_hashes"]
            
            # Verify the hash is correct
            expected_hash = hashlib.sha256(b"content").hexdigest()
            assert manifest["artifact_hashes"]["test.txt"] == expected_hash
        finally:
            update_state.PROJECT_ROOT = original_root

def test_update_manifest():
    """Test that update_manifest writes correct YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.yaml"
        
        test_data = {
            "artifact_hashes": {"test.txt": "abc123"},
            "version": "1.0"
        }
        
        update_manifest(test_data, manifest_path)
        
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            loaded_data = yaml.safe_load(f)
        
        assert loaded_data == test_data
