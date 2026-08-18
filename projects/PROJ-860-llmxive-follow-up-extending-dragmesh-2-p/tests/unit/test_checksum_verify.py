import os
import sys
import tempfile
import yaml
import pytest
from pathlib import Path
import hashlib

# Add parent directory to path to import from code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from checksum_verify import compute_sha256, scan_directory, load_existing_checksums, save_checksums, update_checksums

def test_compute_sha256():
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        hash_val = compute_sha256(temp_path)
        expected = hashlib.sha256(b"test content").hexdigest()
        assert hash_val == expected
    finally:
        os.unlink(temp_path)

def test_compute_sha256_missing_file():
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/file.txt")

def test_scan_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        Path(tmpdir, "file1.txt").touch()
        Path(tmpdir, "file2.py").touch()
        Path(tmpdir, "subdir").mkdir()
        Path(tmpdir, "subdir", "file3.txt").touch()
        Path(tmpdir, ".hidden").touch()
        Path(tmpdir, "__pycache__").mkdir()
        Path(tmpdir, "__pycache__", "cache.pyc").touch()

        files = scan_directory(tmpdir)
        # Should not include hidden or __pycache__
        assert len(files) == 4 # file1, file2, file3, and maybe the dir if logic was different, but rglob skips dirs
        # Check specific files
        assert any("file1.txt" in f for f in files)
        assert any("file2.py" in f for f in files)
        assert any("file3.txt" in f for f in files)
        assert not any(".hidden" in f for f in files)
        assert not any("__pycache__" in f for f in files)

def test_scan_directory_with_extension():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file1.txt").touch()
        Path(tmpdir, "file2.py").touch()
        
        files = scan_directory(tmpdir, extensions=[".txt"])
        assert len(files) == 1
        assert "file1.txt" in files[0]

def test_save_and_load_checksums():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir, "state.yaml")
        checksums = {
            "data_raw": {"file1.txt": "abc123"},
            "data_generated": {"file2.txt": "def456"}
        }
        
        save_checksums(str(state_file), checksums)
        
        loaded = load_existing_checksums(str(state_file))
        assert loaded == checksums

def test_update_checksums():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir, "test.txt")
        file_path.write_text("hello world")
        
        result = update_checksums(tmpdir, {})
        assert len(result) == 1
        assert "test.txt" in result[list(result.keys())[0]] # This check is slightly loose due to relative path logic in real code, but verifies presence
        # More precise check:
        rel_key = os.path.relpath(str(file_path), start=os.getcwd())
        # The function returns a dict of {rel_path: hash}
        # But in the main logic, it's assigned to a category.
        # Let's test the function directly as intended in the helper
        computed = compute_sha256(str(file_path))
        assert result[rel_key] == computed