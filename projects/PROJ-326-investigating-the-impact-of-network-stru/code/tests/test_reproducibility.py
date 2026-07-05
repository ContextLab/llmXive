import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import random

from code.src.utils.reproducibility import (
    ensure_data_directory,
    generate_run_id,
    inject_seed_to_log,
    get_latest_run_seed,
    verify_reproducibility
)
from code.src.utils.logging import get_run_log, clear_run_log

@pytest.fixture
def temp_log_path():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_inject_seed_creates_log(temp_log_path):
    """Test that inject_seed_to_log creates the run_log.json file."""
    seed = 42
    inject_seed_to_log(seed=seed, data_dir=temp_log_path)
    
    log_file = temp_log_path / "run_log.json"
    assert log_file.exists(), "run_log.json should be created"
    
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    assert isinstance(log_data, list), "Log should be a list"
    assert len(log_data) == 1, "Should have one entry"
    assert log_data[0]["seed"] == seed

def test_inject_seed_appends_to_existing_log(temp_log_path):
    """Test that inject_seed_to_log appends to existing log."""
    # Create initial log
    seed1 = 123
    inject_seed_to_log(seed=seed1, data_dir=temp_log_path)
    
    # Add another seed
    seed2 = 456
    inject_seed_to_log(seed=seed2, data_dir=temp_log_path)
    
    log_file = temp_log_path / "run_log.json"
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    assert len(log_data) == 2, "Should have two entries"
    assert log_data[0]["seed"] == seed1
    assert log_data[1]["seed"] == seed2

def test_inject_seed_sets_global_seeds(temp_log_path):
    """Test that inject_seed_to_log actually sets the random seed."""
    seed = 999
    
    # Inject seed
    inject_seed_to_log(seed=seed, data_dir=temp_log_path)
    
    # Generate a random number
    random_value = random.random()
    
    # Reset seed and generate again
    random.seed(seed)
    expected_value = random.random()
    
    assert random_value == expected_value, "Random state should be reproducible"

def test_get_latest_run_seed(temp_log_path):
    """Test retrieving the latest seed from the log."""
    seed1 = 111
    seed2 = 222
    seed3 = 333
    
    inject_seed_to_log(seed=seed1, data_dir=temp_log_path)
    inject_seed_to_log(seed=seed2, data_dir=temp_log_path)
    inject_seed_to_log(seed=seed3, data_dir=temp_log_path)
    
    latest_seed = get_latest_run_seed(temp_log_path)
    assert latest_seed == seed3, "Should return the most recent seed"

def test_verify_reproducibility(temp_log_path):
    """Test verifying a specific seed exists in the log."""
    seed = 777
    inject_seed_to_log(seed=seed, data_dir=temp_log_path)
    
    assert verify_reproducibility(seed, temp_log_path), "Seed should be verified"
    assert not verify_reproducibility(999, temp_log_path), "Different seed should fail"

def test_extra_metadata_logged(temp_log_path):
    """Test that extra metadata is included in the log entry."""
    seed = 555
    metadata = {
        "experiment": "test_run",
        "parameters": {"alpha": 0.5, "beta": 0.3}
    }
    
    inject_seed_to_log(seed=seed, data_dir=temp_log_path, metadata=metadata)
    
    log_data = get_run_log(temp_log_path)
    entry = log_data[0]
    
    assert entry["metadata"]["experiment"] == "test_run"
    assert entry["metadata"]["parameters"]["alpha"] == 0.5

def test_generate_run_id_format():
    """Test that run ID has the expected format."""
    run_id = generate_run_id()
    parts = run_id.split("_")
    
    assert len(parts) == 3, "Run ID should have 3 parts"
    assert len(parts[2]) == 4, "Random component should be 4 digits"
    # Check timestamp format (YYYYMMDD_HHMMSS)
    assert len(parts[0]) == 8 and len(parts[1]) == 6, "Timestamp format incorrect"
