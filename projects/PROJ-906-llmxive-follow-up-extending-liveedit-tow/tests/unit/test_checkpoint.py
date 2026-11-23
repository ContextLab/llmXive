"""
Unit tests for the checkpointing infrastructure.
"""
import os
import json
import torch
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module under test
try:
    from utils.checkpoint import CheckpointManager, save_state, load_state
except ImportError:
    # Fallback for test execution context
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from utils.checkpoint import CheckpointManager, save_state, load_state

@pytest.fixture
def temp_checkpoint_dir():
    """Creates a temporary directory for checkpoints."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def test_save_state_basic(temp_checkpoint_dir):
    """Tests basic state saving functionality."""
    run_id = "test_run_001"
    manager = CheckpointManager(run_id, checkpoint_dir=temp_checkpoint_dir)
    
    state = {
        "step": 10,
        "loss": 0.5,
        "model_weights": torch.tensor([1.0, 2.0, 3.0]),
        "metadata": {"key": "value"}
    }
    
    manager.save_state(state)
    
    expected_path = os.path.join(temp_checkpoint_dir, f"{run_id}.json")
    assert os.path.exists(expected_path), f"Checkpoint file not created at {expected_path}"
    
    with open(expected_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["step"] == 10
    assert loaded["loss"] == 0.5
    assert loaded["metadata"] == {"key": "value"}
    # Check tensor conversion
    assert np.allclose(np.array(loaded["model_weights"]), np.array([1.0, 2.0, 3.0]))

def test_load_state_success(temp_checkpoint_dir):
    """Tests successful state loading."""
    run_id = "test_run_002"
    manager = CheckpointManager(run_id, checkpoint_dir=temp_checkpoint_dir)
    
    state = {
        "step": 20,
        "accuracy": 0.95
    }
    manager.save_state(state)
    
    loaded_state = manager.load_state()
    
    assert loaded_state is not None
    assert loaded_state["step"] == 20
    assert loaded_state["accuracy"] == 0.95

def test_load_state_missing_file(temp_checkpoint_dir):
    """Tests loading when checkpoint file does not exist."""
    run_id = "test_run_003"
    manager = CheckpointManager(run_id, checkpoint_dir=temp_checkpoint_dir)
    
    loaded_state = manager.load_state()
    
    assert loaded_state is None

def test_delete_checkpoint(temp_checkpoint_dir):
    """Tests checkpoint deletion."""
    run_id = "test_run_004"
    manager = CheckpointManager(run_id, checkpoint_dir=temp_checkpoint_dir)
    
    state = {"step": 30}
    manager.save_state(state)
    
    expected_path = os.path.join(temp_checkpoint_dir, f"{run_id}.json")
    assert os.path.exists(expected_path)
    
    deleted = manager.delete_checkpoint()
    assert deleted is True
    assert not os.path.exists(expected_path)

def test_convenience_functions(temp_checkpoint_dir):
    """Tests the standalone save_state and load_state functions."""
    run_id = "test_run_005"
    
    state = {
        "step": 40,
        "data": [1, 2, 3]
    }
    
    save_state(state, run_id, checkpoint_dir=temp_checkpoint_dir)
    
    loaded = load_state(run_id, checkpoint_dir=temp_checkpoint_dir)
    
    assert loaded is not None
    assert loaded["step"] == 40
    assert loaded["data"] == [1, 2, 3]
