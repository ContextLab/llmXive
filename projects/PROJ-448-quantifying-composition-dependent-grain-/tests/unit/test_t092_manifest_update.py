"""
Unit tests for T092: Manifest update functionality.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.update_manifest_ground_truth import (
    calculate_sha256,
    load_manifest,
    save_manifest,
    update_manifest_with_ground_truth
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_csv_file(temp_data_dir):
    """Create a sample CSV file for testing."""
    csv_path = temp_data_dir / "test_data.csv"
    content = """col1,col2,col3
1,2,3
4,5,6
7,8,9
"""
    csv_path.write_text(content)
    return csv_path

def test_calculate_sha256(sample_csv_file):
    """Test SHA256 calculation."""
    checksum = calculate_sha256(sample_csv_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_calculate_sha256_file_not_found():
    """Test checksum calculation on non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(Path("/nonexistent/file.csv"))

def test_load_manifest_new(temp_data_dir):
    """Test loading a non-existent manifest creates a new one."""
    manifest_path = temp_data_dir / "manifest.json"
    
    # Simulate new manifest creation
    manifest = {
        "version": "1.0",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "entries": []
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    
    loaded = load_manifest()
    assert loaded["version"] == "1.0"
    assert len(loaded["entries"]) == 0

def test_update_manifest_creates_entry(temp_data_dir):
    """Test that updating manifest creates a new entry."""
    manifest_path = temp_data_dir / "manifest.json"
    
    # Create initial manifest
    initial_manifest = {
        "version": "1.0",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "entries": []
    }
    with open(manifest_path, "w") as f:
        json.dump(initial_manifest, f)
    
    # Mock the global paths
    import code.config as config
    original_manifest_path = config.DATA_MANIFEST_PATH
    config.DATA_MANIFEST_PATH = manifest_path
    
    try:
        update_manifest_with_ground_truth("dummy_checksum_1234567890abcdef")
        
        with open(manifest_path, "r") as f:
            updated_manifest = json.load(f)
        
        assert len(updated_manifest["entries"]) == 1
        assert updated_manifest["entries"][0]["id"] == "generated_ground_truth"
        assert updated_manifest["entries"][0]["checksum"] == "dummy_checksum_1234567890abcdef"
    finally:
        config.DATA_MANIFEST_PATH = original_manifest_path

def test_update_manifest_no_duplicate(temp_data_dir):
    """Test that updating manifest does not create duplicate entries."""
    manifest_path = temp_data_dir / "manifest.json"
    
    # Create manifest with existing entry
    initial_manifest = {
        "version": "1.0",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "entries": [
            {
                "id": "generated_ground_truth",
                "checksum": "old_checksum"
            }
        ]
    }
    with open(manifest_path, "w") as f:
        json.dump(initial_manifest, f)
    
    # Mock the global paths
    import code.config as config
    original_manifest_path = config.DATA_MANIFEST_PATH
    config.DATA_MANIFEST_PATH = manifest_path
    
    try:
        update_manifest_with_ground_truth("new_checksum_1234567890abcdef")
        
        with open(manifest_path, "r") as f:
            updated_manifest = json.load(f)
        
        # Should still have only 1 entry
        assert len(updated_manifest["entries"]) == 1
        assert updated_manifest["entries"][0]["checksum"] == "new_checksum_1234567890abcdef"
    finally:
        config.DATA_MANIFEST_PATH = original_manifest_path