import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Import the functions we are testing
from hygiene import audit_data_integrity, update_state_file, find_state_file

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def valid_csv_path(temp_data_dir):
    """Create a valid CSV file with no null values."""
    csv_path = Path(temp_data_dir) / "data" / "processed" / "raw_calibration.csv"
    data = {
        "device_id": ["ibmq_manila", "ibmq_quito", "ibmq_belem"],
        "timestamp": ["2024-01-01T00:00:00", "2024-01-02T00:00:00", "2024-01-03T00:00:00"],
        "t1_mean": [100.5, 120.3, 95.8],
        "t2_mean": [80.2, 90.1, 75.5],
        "cx_error_mean": [0.01, 0.015, 0.012],
        "readout_error_mean": [0.05, 0.06, 0.04],
        "coupling_map": ["[[0,1],[1,2]]", "[[0,1],[2,3]]", "[[0,1],[1,2],[2,3]]"]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def csv_with_nulls_path(temp_data_dir):
    """Create a CSV file with null values in critical columns."""
    csv_path = Path(temp_data_dir) / "data" / "processed" / "raw_calibration.csv"
    data = {
        "device_id": ["ibmq_manila", "ibmq_quito", "ibmq_belem", "ibmq_nairobi"],
        "timestamp": ["2024-01-01T00:00:00", "2024-01-02T00:00:00", "2024-01-03T00:00:00", "2024-01-04T00:00:00"],
        "t1_mean": [100.5, np.nan, 95.8, 110.2],  # nan in second row
        "t2_mean": [80.2, 90.1, np.nan, 85.5],    # nan in third row
        "cx_error_mean": [0.01, 0.015, 0.012, np.nan], # nan in fourth row
        "readout_error_mean": [0.05, 0.06, 0.04, 0.055],
        "coupling_map": ["[[0,1],[1,2]]", "[[0,1],[2,3]]", "[[0,1],[1,2],[2,3]]", "[[0,1]]"]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def state_file_path(temp_data_dir):
    """Create a mock state file."""
    state_dir = Path(temp_data_dir) / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "PROJ-163-exploring-the-role-of-network-structure-.yaml"
    state_file.write_text("project_id: PROJ-163\nartifact_hashes: {}\n")
    return state_file

def test_audit_valid_data(valid_csv_path, caplog):
    """Test that valid data passes the audit without warnings."""
    excluded = audit_data_integrity(valid_csv_path)
    
    assert len(excluded) == 0, "Valid data should not produce any excluded devices"
    assert "Data integrity check passed" in caplog.text

def test_audit_null_values(csv_with_nulls_path, caplog):
    """Test that null values are detected and devices are excluded."""
    excluded = audit_data_integrity(csv_with_nulls_path)
    
    # We expect 3 devices to be excluded (one for each null in critical columns)
    assert len(excluded) == 3, f"Expected 3 excluded devices, got {len(excluded)}"
    assert "ibmq_quito" in excluded
    assert "ibmq_belem" in excluded
    assert "ibmq_nairobi" in excluded
    
    assert "Excluding device" in caplog.text
    assert "null/NaN" in caplog.text

def test_audit_missing_file(caplog):
    """Test behavior when CSV file does not exist."""
    excluded = audit_data_integrity("nonexistent/path.csv")
    
    assert len(excluded) == 0
    assert "CSV file not found" in caplog.text

def test_audit_updates_state(csv_with_nulls_path, state_file_path, caplog):
    """Test that excluded devices are recorded in the state file."""
    # Run audit
    excluded = audit_data_integrity(csv_with_nulls_path)
    
    # Update state file
    update_state_file(excluded, state_file_path)
    
    # Verify state file was updated
    import yaml
    with open(state_file_path, "r") as f:
        state = yaml.safe_load(f)
    
    assert "artifact_hashes" in state
    assert "data_integrity_audit" in state["artifact_hashes"]
    assert "excluded_devices" in state["artifact_hashes"]["data_integrity_audit"]
    assert set(state["artifact_hashes"]["data_integrity_audit"]["excluded_devices"]) == set(excluded)
    assert "exclusion_reason" in state["artifact_hashes"]["data_integrity_audit"]
    assert state["artifact_hashes"]["data_integrity_audit"]["exclusion_reason"] == "null_or_nan_in_critical_columns"

def test_empty_csv(temp_data_dir, caplog):
    """Test behavior with an empty CSV (only headers)."""
    csv_path = Path(temp_data_dir) / "data" / "processed" / "raw_calibration.csv"
    csv_path.write_text("device_id,timestamp,t1_mean,t2_mean,cx_error_mean,readout_error_mean,coupling_map\n")
    
    excluded = audit_data_integrity(str(csv_path))
    
    assert len(excluded) == 0
    assert "Data integrity check passed" in caplog.text
