"""
Unit tests for T020: Save raw data with checksums.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import hashlib
import yaml
import pytest
import pandas as pd

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code_00_save_raw_data import (
    load_or_fetch_real_data,
    save_raw_data,
    compute_and_save_checksum,
    update_project_state,
    main,
    RAW_DATA_FILE,
    CHECKSUM_FILE,
    PROJECT_STATE_FILE,
    DATA_RAW_DIR,
    STATE_DIR,
    CHECKSUM_DIR
)

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    data_raw = tmp_path / "data" / "raw"
    state_projects = tmp_path / "state" / "projects"
    checksum_dir = state_projects / "checksums"
    
    data_raw.mkdir(parents=True, exist_ok=True)
    state_projects.mkdir(parents=True, exist_ok=True)
    checksum_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock the global paths
    original_raw = RAW_DATA_FILE
    original_checksum = CHECKSUM_FILE
    original_state = PROJECT_STATE_FILE
    original_data_raw = DATA_RAW_DIR
    original_state_dir = STATE_DIR
    original_checksum_dir = CHECKSUM_DIR

    # Temporarily override the module-level constants
    import code_00_save_raw_data as module
    module.RAW_DATA_FILE = data_raw / "polymer_blend_raw.csv"
    module.CHECKSUM_FILE = checksum_dir / "polymer_blend_raw.json"
    module.PROJECT_STATE_FILE = state_projects / "PROJ-122-identifying-structure-property-relations.yaml"
    module.DATA_RAW_DIR = data_raw
    module.STATE_DIR = state_projects
    module.CHECKSUM_DIR = checksum_dir

    yield tmp_path

    # Restore original paths
    module.RAW_DATA_FILE = original_raw
    module.CHECKSUM_FILE = original_checksum
    module.PROJECT_STATE_FILE = original_state
    module.DATA_RAW_DIR = original_data_raw
    module.STATE_DIR = original_state_dir
    module.CHECKSUM_DIR = original_checksum_dir

def test_save_raw_data_creates_file(temp_project_root):
    """Test that save_raw_data creates the CSV file."""
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    file_path = save_raw_data(df)
    
    assert file_path.exists()
    assert file_path.suffix == ".csv"
    
    # Verify content
    loaded_df = pd.read_csv(file_path)
    assert len(loaded_df) == 3
    assert list(loaded_df.columns) == ["col1", "col2"]

def test_compute_and_save_checksum(temp_project_root):
    """Test that compute_and_save_checksum creates a valid checksum file."""
    # First, save a file
    df = pd.DataFrame({"x": [1, 2, 3]})
    save_raw_data(df)
    
    # Compute checksum
    checksum_data = compute_and_save_checksum(RAW_DATA_FILE)
    
    assert CHECKSUM_FILE.exists()
    assert "checksum" in checksum_data
    assert "algorithm" in checksum_data
    assert checksum_data["algorithm"] == "sha256"
    assert "timestamp" in checksum_data
    assert "file_size_bytes" in checksum_data
    
    # Verify checksum manually
    with open(RAW_DATA_FILE, "rb") as f:
        expected_hash = hashlib.sha256(f.read()).hexdigest()
    assert checksum_data["checksum"] == expected_hash

def test_update_project_state(temp_project_root):
    """Test that update_project_state updates the YAML file correctly."""
    checksum_data = {
        "checksum": "abc123",
        "timestamp": "2023-01-01T00:00:00"
    }
    
    update_project_state(checksum_data)
    
    assert PROJECT_STATE_FILE.exists()
    
    with open(PROJECT_STATE_FILE, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "artifacts" in state
    assert "polymer_blend_raw" in state["artifacts"]
    assert state["artifacts"]["polymer_blend_raw"]["checksum"] == "abc123"
    assert state["artifacts"]["polymer_blend_raw"]["path"] == "data/raw/polymer_blend_raw.csv"

def test_load_or_fetch_real_data_fails_without_data(temp_project_root, monkeypatch):
    """Test that load_or_fetch_real_data raises an error if no data is available."""
    # Ensure no file exists
    if RAW_DATA_FILE.exists():
        RAW_DATA_FILE.unlink()
    
    # Mock requests.get to fail
    def mock_get(*args, **kwargs):
        raise Exception("Network error")
    
    import code_00_save_raw_data as module
    monkeypatch.setattr(module, 'requests', type('obj', (object,), {'get': mock_get}))
    
    with pytest.raises(RuntimeError, match="Could not load or fetch real data"):
        load_or_fetch_real_data()