import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.scripts.inject_seed import main, verify_seeds, load_existing_log

def test_verify_seeds_pass():
    """Test that verify_seeds returns PASS when seeds match."""
    config = {"global_seed": 42}
    log_entries = [
        {
            "run_id": "test_run",
            "seeds": {"global": 42, "generator": 43, "simulation": 44}
        }
    ]
    result = verify_seeds(config, log_entries)
    assert result["verification_status"] == "PASS"

def test_verify_seeds_fail_mismatch():
    """Test that verify_seeds returns FAIL when seeds mismatch."""
    config = {"global_seed": 100}
    log_entries = [
        {
            "run_id": "test_run",
            "seeds": {"global": 42, "generator": 43, "simulation": 44}
        }
    ]
    result = verify_seeds(config, log_entries)
    assert result["verification_status"] == "FAIL"

def test_verify_seeds_fail_no_log():
    """Test that verify_seeds returns FAIL when no log entries exist."""
    config = {"global_seed": 42}
    log_entries = []
    result = verify_seeds(config, log_entries)
    assert result["verification_status"] == "FAIL"

def test_verify_seeds_fail_no_config_seed():
    """Test that verify_seeds returns FAIL when global_seed is missing in config."""
    config = {}
    log_entries = [
        {
            "run_id": "test_run",
            "seeds": {"global": 42}
        }
    ]
    result = verify_seeds(config, log_entries)
    assert result["verification_status"] == "FAIL"

def test_main_creates_log_on_missing_config():
    """Test that main creates a FAIL log if config is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "missing_config.yaml"
        log_path = Path(tmpdir) / "run_log.json"
        
        # Run main with missing config
        sys.argv = ['inject_seed', '--config', str(config_path), '--output', str(log_path)]
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
        
        # Check log file created with FAIL status
        assert log_path.exists()
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["verification_status"] == "FAIL"
        assert "error" in data[0]

def test_main_successfully_injects_seed():
    """Test that main successfully injects seeds and verifies them."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        log_path = Path(tmpdir) / "run_log.json"
        
        # Create a simple config file
        config_content = """
        global_seed: 123
        simulation_timeout_seconds: 3600
        topology_targets: {}
        simulation_params: {}
        """
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        sys.argv = ['inject_seed', '--config', str(config_path), '--output', str(log_path)]
        
        # Should exit 0
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        
        # Check log file
        assert log_path.exists()
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["verification_status"] == "PASS"
        assert data[0]["seeds"]["global"] == 123
        assert data[0]["seeds"]["generator"] == 124
        assert data[0]["seeds"]["simulation"] == 125
        assert data[0]["run_id"].startswith("run_")
