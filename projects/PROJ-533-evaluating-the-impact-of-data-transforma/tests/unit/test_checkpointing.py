"""
Unit tests for checkpointing functionality.
"""
import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.checkpointing import (
    save_state,
    load_state,
    delete_checkpoint,
    has_checkpoint,
    list_checkpoints,
    ensure_checkpoint_dir,
    get_checkpoint_path
)

@pytest.fixture
def temp_checkpoint_dir():
    """Create a temporary checkpoint directory for testing."""
    temp_dir = tempfile.mkdtemp()
    original_checkpoint_dir = Path("results/checkpoints")
    
    # Save original
    if original_checkpoint_dir.exists():
        original_checkpoint_dir.rename(Path(temp_dir) / "original_checkpoints")
    
    # Create new temp directory
    test_checkpoint_dir = Path(temp_dir) / "results" / "checkpoints"
    test_checkpoint_dir.mkdir(parents=True)
    
    # Temporarily override the module's checkpoint dir
    import code.utils.checkpointing as cp_module
    original_dir = cp_module.CHECKPOINT_DIR
    cp_module.CHECKPOINT_DIR = test_checkpoint_dir
    cp_module.RESULTS_DIR = test_checkpoint_dir.parent
    
    yield test_checkpoint_dir
    
    # Restore original
    cp_module.CHECKPOINT_DIR = original_dir
    cp_module.RESULTS_DIR = original_checkpoint_dir.parent
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_save_state_creates_checkpoint(temp_checkpoint_dir):
    """Test that save_state creates a valid checkpoint file."""
    run_id = "test_run_1"
    step = "initialization"
    data = {
        "current_dataset_id": "dataset_001",
        "last_seed": 42,
        "error_counts": {"missing": 0, "filter": 1}
    }
    
    save_state(run_id, step, data)
    
    checkpoint_path = get_checkpoint_path(run_id)
    assert checkpoint_path.exists(), "Checkpoint file was not created"
    
    with open(checkpoint_path, 'r') as f:
        saved_state = json.load(f)
    
    assert saved_state["run_id"] == run_id
    assert saved_state["step"] == step
    assert saved_state["current_dataset_id"] == data["current_dataset_id"]
    assert saved_state["last_seed"] == data["last_seed"]
    assert saved_state["error_counts"] == data["error_counts"]

def test_load_state_returns_correct_data(temp_checkpoint_dir):
    """Test that load_state returns the correct data."""
    run_id = "test_run_2"
    step = "processing"
    data = {
        "current_dataset_id": "dataset_002",
        "last_seed": 123,
        "error_counts": {"missing": 2, "filter": 0}
    }
    
    save_state(run_id, step, data)
    loaded_state = load_state(run_id)
    
    assert loaded_state is not None
    assert loaded_state["run_id"] == run_id
    assert loaded_state["step"] == step
    assert loaded_state["current_dataset_id"] == data["current_dataset_id"]
    assert loaded_state["last_seed"] == data["last_seed"]
    assert loaded_state["error_counts"] == data["error_counts"]

def test_load_state_returns_none_for_missing_checkpoint(temp_checkpoint_dir):
    """Test that load_state returns None for non-existent checkpoint."""
    loaded_state = load_state("non_existent_run")
    assert loaded_state is None

def test_delete_checkpoint_removes_file(temp_checkpoint_dir):
    """Test that delete_checkpoint removes the checkpoint file."""
    run_id = "test_run_3"
    data = {
        "current_dataset_id": "dataset_003",
        "last_seed": 999,
        "error_counts": {}
    }
    
    save_state(run_id, "test", data)
    assert has_checkpoint(run_id)
    
    result = delete_checkpoint(run_id)
    assert result is True
    assert not has_checkpoint(run_id)

def test_delete_checkpoint_returns_false_for_missing(temp_checkpoint_dir):
    """Test that delete_checkpoint returns False for non-existent checkpoint."""
    result = delete_checkpoint("non_existent_run")
    assert result is False

def test_has_checkpoint(temp_checkpoint_dir):
    """Test has_checkpoint function."""
    run_id = "test_run_4"
    data = {
        "current_dataset_id": "dataset_004",
        "last_seed": 555,
        "error_counts": {}
    }
    
    assert not has_checkpoint(run_id)
    save_state(run_id, "test", data)
    assert has_checkpoint(run_id)
    delete_checkpoint(run_id)
    assert not has_checkpoint(run_id)

def test_list_checkpoints(temp_checkpoint_dir):
    """Test list_checkpoints function."""
    run_ids = ["run_a", "run_b", "run_c"]
    
    for run_id in run_ids:
        save_state(run_id, "test", {
            "current_dataset_id": f"dataset_{run_id}",
            "last_seed": 1,
            "error_counts": {}
        })
    
    checkpoints = list_checkpoints()
    assert set(checkpoints) == set(run_ids)

def test_save_state_with_invalid_data(temp_checkpoint_dir):
    """Test that save_state raises ValueError for invalid data."""
    with pytest.raises(ValueError):
        save_state("test_run", "step", "invalid_data")
    
    with pytest.raises(ValueError):
        save_state("test_run", "step", [1, 2, 3])

def test_atomic_write(temp_checkpoint_dir):
    """Test that checkpoint files are written atomically."""
    run_id = "test_atomic"
    data = {
        "current_dataset_id": "dataset_atomic",
        "last_seed": 777,
        "error_counts": {}
    }
    
    save_state(run_id, "test", data)
    
    # Verify no temp files remain
    temp_files = list(temp_checkpoint_dir.glob("*.tmp"))
    assert len(temp_files) == 0, "Temp files should be cleaned up"