import json
import os
import tempfile
from pathlib import Path
import pytest

from code.src.utils.reproducibility import (
    inject_seed_to_log,
    get_latest_run_seed,
    verify_reproducibility,
    generate_run_id
)
from code.src.utils.config import load_config

@pytest.fixture
def temp_config_file():
    """Create a temporary config file with a known seed."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("global_seed: 42\n")
        f.write("topology_target: 100\n")
        f.write("simulation_timeout_seconds: 60\n")
        return f.name

@pytest.fixture
def temp_log_file():
    """Create a temporary log file path."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    return path

def test_inject_seed_creates_log(temp_config_file, temp_log_file):
    """Test that inject_seed_to_log creates the log file with correct seeds."""
    result = inject_seed_to_log(temp_config_file, temp_log_file)
    
    assert Path(temp_log_file).exists()
    assert "seeds" in result
    assert result["seeds"]["global_random"] == 42
    assert result["verification"]["status"] == "passed"
    
    # Verify file contents
    with open(temp_log_file, 'r') as f:
        data = json.load(f)
    assert data["seeds"]["global_random"] == 42

def test_inject_seed_updates_existing_log(temp_config_file, temp_log_file):
    """Test that inject_seed_to_log updates an existing log correctly."""
    # Create initial log
    initial_data = {"run_id": "initial", "seeds": {"old": 123}}
    with open(temp_log_file, 'w') as f:
        json.dump(initial_data, f)
        
    result = inject_seed_to_log(temp_config_file, temp_log_file)
    
    assert result["seeds"]["global_random"] == 42
    assert "old" not in result["seeds"]  # Overwritten by new logic
    assert result["verification"]["status"] == "passed"

def test_inject_seed_missing_config():
    """Test that inject_seed_to_log fails if config is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = os.path.join(tmpdir, "missing.yaml")
        with pytest.raises(FileNotFoundError):
            inject_seed_to_log(non_existent, os.path.join(tmpdir, "log.json"))

def test_inject_seed_missing_seed_key(temp_log_file):
    """Test that inject_seed_to_log fails if config lacks global_seed."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("topology_target: 100\n")
        config_path = f.name
        
    try:
        with pytest.raises(KeyError):
            inject_seed_to_log(config_path, temp_log_file)
    finally:
        os.unlink(config_path)

def test_get_latest_run_seed(temp_config_file, temp_log_file):
    """Test retrieving the seed from the log."""
    inject_seed_to_log(temp_config_file, temp_log_file)
    seed = get_latest_run_seed(temp_log_file)
    assert seed == 42

def test_get_latest_run_seed_missing_file():
    """Test retrieving seed from non-existent file returns None."""
    seed = get_latest_run_seed("/non/existent/path.json")
    assert seed is None

def test_verify_reproducibility_success(temp_config_file, temp_log_file):
    """Test successful verification."""
    inject_seed_to_log(temp_config_file, temp_log_file)
    assert verify_reproducibility(temp_config_file, temp_log_file) is True

def test_verify_reproducibility_failure(temp_log_file):
    """Test verification failure when log is missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("global_seed: 42\n")
        config_path = f.name
    try:
        assert verify_reproducibility(config_path, temp_log_file) is False
    finally:
        os.unlink(config_path)

def test_generate_run_id():
    """Test that run ID generation creates a string."""
    run_id = generate_run_id()
    assert isinstance(run_id, str)
    assert run_id.startswith("run_")
