import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from filter import validate_endpoints, write_sample_size_status, write_filter_log

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'smiles': ['CC(=O)OC1=CC=CC=C1C(=O)O', 'CC1=C(C=C(C=C1)C)C(=O)O', 'CC(C)C1=CC=C(C=C1)C(=O)O'],
        'nuc_AR': [1.0, 0.0, 1.0],
        'nuc_AhR': [0.0, 1.0, 0.0],
        'nuc_ER': [1.0, 1.0, 0.0]
    }
    return pd.DataFrame(data)

def test_validate_endpoints_counts_correctly(sample_data):
    """Test that validate_endpoints correctly counts rows per endpoint."""
    result = validate_endpoints(sample_data)
    
    assert "endpoint_counts" in result
    assert result["endpoint_counts"]["nuc_AR"] == 3
    assert result["endpoint_counts"]["nuc_AhR"] == 3
    assert result["endpoint_counts"]["nuc_ER"] == 3
    assert result["total_rows"] == 3

def test_write_sample_size_status_ok():
    """Test writing sample size status when n >= 50."""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_path = os.path.join(tmpdir, "status.json")
        write_sample_size_status(100, status_path)
        
        with open(status_path, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "OK"

def test_write_sample_size_status_skip():
    """Test writing sample size status when n < 50."""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_path = os.path.join(tmpdir, "status.json")
        write_sample_size_status(25, status_path)
        
        with open(status_path, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "SKIP_STATS"

def test_write_filter_log_warning():
    """Test writing filter log with warning for low sample size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "filter_log.txt")
        validation_result = {
            "total_rows": 25,
            "endpoint_counts": {"nuc_AR": 25}
        }
        write_filter_log(log_path, validation_result)
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "WARNING: Low Sample Size (n < 50)" in content
        assert "status: OK" not in content

def test_write_filter_log_ok():
    """Test writing filter log with OK status for sufficient sample size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "filter_log.txt")
        validation_result = {
            "total_rows": 100,
            "endpoint_counts": {"nuc_AR": 100}
        }
        write_filter_log(log_path, validation_result)
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "status: OK" in content
        assert "WARNING: Low Sample Size (n < 50)" not in content