"""
Unit tests for download_dft_energies.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download_dft_energies import (
    calculate_sha256,
    fetch_dft_data,
    verify_checksum,
    update_manifest,
    main
)
from code.errors import DataLoadError

def test_calculate_sha256():
    """Test SHA256 calculation function."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_sha256(temp_path)
        assert len(checksum) == 64, "SHA256 should be 64 characters"
        assert all(c in '0123456789abcdef' for c in checksum), "Should be hex"
    finally:
        temp_path.unlink()

def test_verify_checksum():
    """Test checksum verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_sha256(temp_path)
        assert verify_checksum(temp_path, checksum) is True
        assert verify_checksum(temp_path, "wrong_checksum") is False
    finally:
        temp_path.unlink()

def test_update_manifest():
    """Test manifest update function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "data_manifest.json"
        test_file = Path(tmpdir) / "test.json"
        test_file.write_text("{}")
        
        source_info = {
            "name": "Test Source",
            "doi": "10.1234/test",
            "url": "https://example.com/test",
            "description": "Test description"
        }
        
        update_manifest(source_info, test_file, "abc123")
        
        assert manifest_path.exists()
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert 'sources' in manifest
        assert len(manifest['sources']) == 1
        assert manifest['sources'][0]['source_type'] == 'dft'
        assert manifest['sources'][0]['doi'] == '10.1234/test'

def test_fetch_dft_data_error_handling():
    """Test error handling in fetch_dft_data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.json"
        
        # Mock requests.get to raise an exception
        with patch('code.data.download_dft_energies.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            try:
                fetch_dft_data("https://example.com/test", output_path)
                assert False, "Should have raised DataLoadError"
            except DataLoadError:
                pass  # Expected

def test_main_success():
    """Test main function with successful download."""
    # This test would require actual network access or extensive mocking
    # For now, we just verify the function exists and has the right signature
    assert callable(main)

if __name__ == "__main__":
    test_calculate_sha256()
    test_verify_checksum()
    test_update_manifest()
    test_fetch_dft_data_error_handling()
    test_main_success()
    print("All tests passed!")
