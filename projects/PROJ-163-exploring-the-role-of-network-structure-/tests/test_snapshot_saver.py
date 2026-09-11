"""
Tests for the snapshot_saver module.
"""
import os
import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from snapshot_saver import compute_sha256, ensure_data_raw_dir, save_backend_snapshot

def test_compute_sha256():
    """Test that SHA256 computation is correct."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name

    try:
        hash_result = compute_sha256(temp_path)
        assert len(hash_result) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in hash_result)
    finally:
        os.unlink(temp_path)

def test_ensure_data_raw_dir_creates_directory():
    """Test that ensure_data_raw_dir creates the directory if it doesn't exist."""
    # Use a temporary directory for testing to avoid polluting the project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        test_raw_dir = Path(tmpdir) / "data" / "raw"
        
        # Mock the function to use our temp dir
        with patch('snapshot_saver.Path') as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.mkdir = MagicMock()
            mock_path_instance.__truediv__ = MagicMock(return_value=mock_path_instance)
            
            # Call the function
            result = ensure_data_raw_dir()
            
            # Verify mkdir was called
            mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_save_backend_snapshot_creates_json_and_checksum():
    """Test that save_backend_snapshot creates a JSON file and a checksum file."""
    test_data = {
        "backend_name": "test_backend",
        "qubits": [{"t1": 100, "t2": 200}],
        "gates": [{"gate": "cx", "error": 0.01}]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        file_path = save_backend_snapshot(
            "test_backend", 
            test_data, 
            output_dir=output_dir
        )
        
        # Check JSON file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".json")
        
        # Check content
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data["backend_name"] == "test_backend"
        
        # Check checksum file exists
        checksum_path = file_path.replace(".json", ".sha256")
        assert os.path.exists(checksum_path)
        
        # Verify checksum content
        with open(checksum_path, 'r') as f:
            checksum_content = f.read().strip()
        
        stored_hash, stored_filename = checksum_content.split("  ")
        assert stored_filename.endswith(".json")
        
        # Verify the hash matches
        computed_hash = compute_sha256(file_path)
        assert stored_hash == computed_hash

def test_save_backend_snapshot_raises_on_empty_data():
    """Test that save_backend_snapshot raises ValueError for empty data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        with pytest.raises(ValueError, match="Cannot save empty or None properties data."):
            save_backend_snapshot("test_backend", {}, output_dir=output_dir)
        
        with pytest.raises(ValueError, match="Cannot save empty or None properties data."):
            save_backend_snapshot("test_backend", None, output_dir=output_dir)
