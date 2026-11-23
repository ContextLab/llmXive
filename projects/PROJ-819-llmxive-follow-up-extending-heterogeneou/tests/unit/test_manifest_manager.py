import json
import hashlib
import tempfile
from pathlib import Path
import pytest

from reproducibility.manifest_manager import (
    calculate_sha256,
    ensure_directories,
    get_files_to_hash,
    generate_manifest,
    save_manifest,
    verify_manifest,
    main
)

def test_calculate_sha256():
    """Test SHA-256 calculation for a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        actual_hash = calculate_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        temp_path.unlink()

def test_ensure_directories():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        ensure_directories(base_path)
        assert (base_path / "hashes").exists()

def test_get_files_to_hash():
    """Test file discovery in target directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create test structure
        (base_path / "data").mkdir()
        (base_path / "code").mkdir()
        (base_path / "data" / "file1.txt").write_text("content1")
        (base_path / "code" / "file2.py").write_text("print('hello')")
        (base_path / "other").mkdir()
        (base_path / "other" / "file3.txt").write_text("content3")
        
        files = get_files_to_hash(base_path, ["data", "code"])
        
        assert len(files) == 2
        paths = [str(f.relative_to(base_path)) for f in files]
        assert "data/file1.txt" in paths
        assert "code/file2.py" in paths
        assert "other/file3.txt" not in paths

def test_generate_manifest():
    """Test manifest generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create test file
        test_file = base_path / "data" / "test.txt"
        test_file.parent.mkdir()
        test_file.write_text("test content")
        
        files = [test_file]
        manifest = generate_manifest(files, base_path)
        
        assert "files" in manifest
        assert len(manifest["files"]) == 1
        assert manifest["files"][0]["path"] == "data/test.txt"
        assert "sha256" in manifest["files"][0]

def test_save_and_verify_manifest():
    """Test saving and verifying manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        state_dir = base_path / "state"
        
        # Create test file
        test_file = base_path / "data" / "test.txt"
        test_file.parent.mkdir()
        test_file.write_text("test content")
        
        files = [test_file]
        manifest = generate_manifest(files, base_path)
        manifest_path = state_dir / "manifest.json"
        
        save_manifest(manifest, manifest_path)
        
        assert verify_manifest(manifest_path, base_path) is True
        
        # Modify file and verify failure
        test_file.write_text("modified content")
        assert verify_manifest(manifest_path, base_path) is False

def test_main_function():
    """Test main function execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a minimal project structure
        base_path = Path(tmpdir)
        (base_path / "data").mkdir()
        (base_path / "code").mkdir()
        (base_path / "data" / "test.txt").write_text("test")
        
        # Change to temp directory to simulate project root
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(base_path)
            
            # Create a minimal manifest_manager.py in the right place
            reproducibility_dir = base_path / "code" / "reproducibility"
            reproducibility_dir.mkdir(parents=True)
            (reproducibility_dir / "__init__.py").write_text("")
            
            # Copy the main function logic here for testing
            from reproducibility.manifest_manager import main as manifest_main
            manifest_main()
            
            assert (base_path / "state" / "manifest.json").exists()
        finally:
            os.chdir(original_cwd)
