import os
import json
import tempfile
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from simulation.logging_utils import ensure_log_directory, log_simulation_run, LOG_DIR, LOG_FILE_NAME

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logging tests."""
    original_dir = LOG_DIR
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override the global LOG_DIR constant for testing
        # Note: In real usage, this would be configured via env or config
        import simulation.logging_utils as utils
        utils.LOG_DIR = tmpdir
        yield tmpdir
        utils.LOG_DIR = original_dir

def test_ensure_log_directory_creates_dir(temp_log_dir):
    """Test that ensure_log_directory creates the directory if it doesn't exist."""
    # The fixture already ensures the dir exists, but we test the function logic
    result_path = ensure_log_directory()
    assert os.path.exists(result_path)
    assert os.path.isdir(result_path)

def test_log_simulation_run_writes_json_line(temp_log_dir):
    """Test that log_simulation_run writes a valid JSON line to the log file."""
    log_simulation_run(
        N=30,
        rho=0.5,
        seed=42,
        duration=1.23,
        vif_max=2.5,
        instance_id="test_123"
    )
    
    log_path = os.path.join(temp_log_dir, LOG_FILE_NAME)
    assert os.path.exists(log_path)
    
    with open(log_path, 'r') as f:
        line = f.readline()
        record = json.loads(line)
        
        assert record["N"] == 30
        assert record["rho"] == 0.5
        assert record["seed"] == 42
        assert abs(record["duration"] - 1.23) < 0.01 # Allow slight float diff
        assert record["vif_max"] == 2.5
        assert record["instance_id"] == "test_123"
        assert "timestamp" in record

def test_log_simulation_run_appends(temp_log_dir):
    """Test that multiple calls append to the log file."""
    log_simulation_run(N=10, rho=0.1, seed=1, duration=0.1, vif_max=1.0, instance_id="first")
    log_simulation_run(N=20, rho=0.2, seed=2, duration=0.2, vif_max=1.5, instance_id="second")
    
    log_path = os.path.join(temp_log_dir, LOG_FILE_NAME)
    with open(log_path, 'r') as f:
        lines = f.readlines()
        
    assert len(lines) == 2
    
    first_record = json.loads(lines[0])
    second_record = json.loads(lines[1])
    
    assert first_record["instance_id"] == "first"
    assert second_record["instance_id"] == "second"