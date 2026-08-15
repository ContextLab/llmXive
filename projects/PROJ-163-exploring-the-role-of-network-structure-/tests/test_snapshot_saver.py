"""
Tests for the Snapshot Saver (Task T016)

Verifies that raw JSON snapshots are saved correctly with timestamps and checksums.
"""
import json
import hashlib
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

# Mock the logger and config to avoid dependency issues in tests
import sys
from unittest.mock import patch, MagicMock

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent))

from snapshot_saver import save_backend_snapshot, compute_sha256, ensure_data_raw_dir

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data/raw."""
    temp_root = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_root)
    
    # Create the expected directory structure
    data_raw = Path("data/raw")
    data_raw.mkdir(parents=True, exist_ok=True)
    
    yield temp_root
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_root)

def test_compute_sha256():
    """Test SHA256 computation."""
    content = "test content"
    expected_hash = hashlib.sha256(b"test content").hexdigest()
    assert compute_sha256(content) == expected_hash

def test_save_backend_snapshot_success(temp_data_dir):
    """Test successful saving of a backend snapshot."""
    device_id = "ibm_test_device"
    properties = {
        "backend_name": "ibm_test_device",
        "last_update_date": datetime.utcnow(),
        "qubits": [{"name": "T1", "value": 100}],
        "coupling_map": [[0, 1], [1, 2]]
    }
    
    result_path = save_backend_snapshot(device_id, properties)
    
    assert os.path.exists(result_path)
    assert result_path.endswith(".json")
    
    # Verify content
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    assert data['device_id'] == device_id
    assert 'fetched_at_utc' in data
    assert data['data']['backend_name'] == device_id
    
    # Verify checksum file exists
    checksum_path = result_path.replace('.json', '.sha256')
    assert os.path.exists(checksum_path)
    
    # Verify checksum content matches
    with open(checksum_path, 'r') as f:
        stored_hash = f.read().split()[0]
    
    with open(result_path, 'r') as f:
        content = f.read()
    
    assert compute_sha256(content) == stored_hash

def test_save_backend_snapshot_empty_properties():
    """Test that saving with empty properties raises ValueError."""
    with pytest.raises(ValueError, match="properties dictionary is empty"):
        save_backend_snapshot("test_device", {})

def test_save_backend_snapshot_custom_timestamp(temp_data_dir):
    """Test saving with a custom timestamp."""
    device_id = "ibm_test_device_2"
    properties = {"backend_name": "ibm_test_device_2"}
    custom_time = datetime(2023, 1, 1, 12, 0, 0)
    
    result_path = save_backend_snapshot(device_id, properties, custom_time)
    
    assert f"20230101_120000" in result_path