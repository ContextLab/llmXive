import os
import json
import tempfile
from pathlib import Path
import pytest

# Mock the config to use a temporary directory for testing
import sys
from unittest.mock import patch

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = Path(tmpdir) / "data"
        data_root.mkdir()
        (data_root / "raw").mkdir()
        (data_root / "processed").mkdir()
        
        # Patch get_path to return our temp directory
        with patch('code.config.get_path') as mock_get_path:
            def side_effect(key):
                if key == "data_root":
                    return str(data_root)
                elif key == "data/.checksum_registry.json":
                    return str(data_root / ".checksum_registry.json")
                return str(data_root / key)
            
            mock_get_path.side_effect = side_effect
            yield data_root

def test_compute_file_checksum(temp_data_dir):
    """Test that compute_file_checksum returns a valid SHA-256 hash."""
    from code.utils.checksum_tracker import compute_file_checksum
    
    test_file = temp_data_dir / "raw" / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 hex string length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_register_and_verify_file(temp_data_dir):
    """Test registering and verifying a file."""
    from code.utils.checksum_tracker import load_registry, save_registry, register_file, verify_file
    
    test_file = temp_data_dir / "raw" / "test.txt"
    test_file.write_text("Test content")
    
    registry = load_registry()
    register_file(test_file, registry)
    save_registry(registry)
    
    # Verify should return True
    assert verify_file(test_file, registry)
    
    # Modify the file and verify should return False
    test_file.write_text("Modified content")
    assert not verify_file(test_file, registry)

def test_initialize_directories(temp_data_dir):
    """Test that initialize_directories creates directories and registry."""
    from code.utils.checksum_tracker import initialize_directories, load_registry
    
    new_dir = temp_data_dir / "new_dir"
    initialize_directories([new_dir])
    
    assert new_dir.exists()
    
    registry = load_registry()
    assert "new_dir" in registry["directories"]

def test_track_directory(temp_data_dir):
    """Test that track_directory registers all files in a directory."""
    from code.utils.checksum_tracker import load_registry, track_directory
    
    # Create some files
    (temp_data_dir / "raw" / "file1.txt").write_text("Content 1")
    (temp_data_dir / "raw" / "subdir").mkdir()
    (temp_data_dir / "raw" / "subdir" / "file2.txt").write_text("Content 2")
    
    track_directory(temp_data_dir / "raw")
    
    registry = load_registry()
    assert "raw/file1.txt" in registry["files"]
    assert "raw/subdir/file2.txt" in registry["files"]
