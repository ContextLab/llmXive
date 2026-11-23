import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(project_root))

from code.data.update_manifest_ground_truth import (
    calculate_sha256,
    load_manifest,
    save_manifest,
    update_manifest_with_ground_truth
)
from code.errors import ManifestError

@pytest.fixture
def temp_manifest_file():
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"sources": []}, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_data_file():
    """Create a temporary data file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("col1,col2\n1,2\n3,4\n")
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_calculate_sha256(temp_data_file):
    """Test SHA-256 calculation."""
    checksum = calculate_sha256(temp_data_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex string length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_load_manifest_existing(temp_manifest_file):
    """Test loading an existing manifest."""
    manifest = load_manifest(temp_manifest_file)
    assert "sources" in manifest
    assert isinstance(manifest["sources"], list)

def test_load_manifest_nonexistent():
    """Test loading a non-existent manifest creates new structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_path = Path(tmpdir) / "nonexistent.json"
        manifest = load_manifest(nonexistent_path)
        assert "sources" in manifest
        assert manifest["sources"] == []

def test_save_manifest(temp_manifest_file):
    """Test saving a manifest."""
    manifest = {"sources": [{"id": "test"}]}
    save_manifest(temp_manifest_file, manifest)
    
    # Verify file was written
    assert temp_manifest_file.exists()
    with open(temp_manifest_file, 'r') as f:
        loaded = json.load(f)
    assert loaded == manifest

def test_update_manifest_with_new_entry(temp_manifest_file, temp_data_file):
    """Test adding a new entry to the manifest."""
    manifest = load_manifest(temp_manifest_file)
    
    generation_params = {"test_param": "value"}
    updated = update_manifest_with_ground_truth(
        manifest, temp_data_file, "test_source", generation_params
    )
    
    assert len(updated["sources"]) == 1
    entry = updated["sources"][0]
    assert entry["source_id"] == "test_source"
    assert entry["source_type"] == "generated"
    assert "checksum" in entry
    assert entry["generation_params"] == generation_params

def test_update_manifest_existing_entry(temp_manifest_file, temp_data_file):
    """Test updating an existing entry in the manifest."""
    # Create initial manifest with entry
    initial_manifest = {
        "sources": [{
            "source_id": "test_source",
            "source_type": "generated",
            "checksum": "old_checksum"
        }]
    }
    with open(temp_manifest_file, 'w') as f:
        json.dump(initial_manifest, f)
    
    manifest = load_manifest(temp_manifest_file)
    updated = update_manifest_with_ground_truth(
        manifest, temp_data_file, "test_source", {"new_param": "value"}
    )
    
    assert len(updated["sources"]) == 1
    entry = updated["sources"][0]
    assert entry["source_id"] == "test_source"
    assert entry["checksum"] != "old_checksum"  # Checksum should be updated
    assert entry["generation_params"]["new_param"] == "value"

def test_update_manifest_missing_file(temp_manifest_file):
    """Test that updating with a missing file raises an error."""
    manifest = load_manifest(temp_manifest_file)
    missing_file = Path("/nonexistent/path/file.csv")
    
    with pytest.raises(FileNotFoundError):
        update_manifest_with_ground_truth(
            manifest, missing_file, "test_source", {}
        )
