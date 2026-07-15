"""
Unit tests for the CheckpointManager.
"""
import os
import tempfile
import torch
import pytest
from pathlib import Path

# Import the module under test
# Adjust import path based on project structure
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.checkpoint import CheckpointManager
from utils.logger import setup_logging


@pytest.fixture
def temp_dir():
    """Creates a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_checkpoint_creation(temp_dir):
    """Test that a checkpoint is created and saved correctly."""
    manager = CheckpointManager(
        checkpoint_dir=temp_dir,
        experiment_id="test_exp",
        save_interval=1
    )
    
    test_state = {"model_weights": torch.tensor([1.0, 2.0]), "step": 5}
    
    manager.save(test_state, step=5, clip_id="clip_001")
    
    path = manager.get_checkpoint_path(5)
    assert path.exists(), "Checkpoint file was not created"
    
    loaded = torch.load(path, map_location="cpu")
    assert loaded["step"] == 5
    assert torch.equal(loaded["state"]["model_weights"], torch.tensor([1.0, 2.0]))
    assert loaded["metadata"]["clip_id"] == "clip_001"


def test_latest_checkpoint_detection(temp_dir):
    """Test that the latest checkpoint is correctly identified."""
    manager = CheckpointManager(
        checkpoint_dir=temp_dir,
        experiment_id="test_exp",
        save_interval=1
    )
    
    # Save checkpoints at different steps
    manager.save({"data": 1}, step=1)
    manager.save({"data": 2}, step=2)
    manager.save({"data": 3}, step=3)
    
    latest = manager.get_latest_checkpoint_path()
    assert latest is not None
    assert "step_3" in latest.name


def test_load_checkpoint(temp_dir):
    """Test loading a checkpoint."""
    manager = CheckpointManager(
        checkpoint_dir=temp_dir,
        experiment_id="test_exp",
        save_interval=1
    )
    
    manager.save({"value": 42}, step=10)
    
    loaded_data = manager.load()
    assert loaded_data is not None
    assert loaded_data["state"]["value"] == 42
    assert loaded_data["step"] == 10


def test_no_checkpoint_exists(temp_dir):
    """Test behavior when no checkpoint exists."""
    manager = CheckpointManager(
        checkpoint_dir=temp_dir,
        experiment_id="test_exp",
        save_interval=1
    )
    
    loaded_data = manager.load()
    assert loaded_data is None


def test_should_save_logic(temp_dir):
    """Test the should_save logic with different intervals."""
    manager = CheckpointManager(
        checkpoint_dir=temp_dir,
        experiment_id="test_exp",
        save_interval=5
    )
    
    # Should save at 0
    assert manager.should_save(0) is True
    # Should not save at 1, 2, 3, 4
    assert manager.should_save(1) is False
    assert manager.should_save(4) is False
    # Should save at 5 (index 4 is 5th item, but logic is (idx+1)%5==0)
    # Wait, logic: if (current_index + 1) % self.save_interval == 0
    # Index 4 -> (4+1)%5 = 0 -> True. Correct.
    assert manager.should_save(4) is True
    
    # With interval 1, should save every time
    manager.save_interval = 1
    assert manager.should_save(100) is True
    assert manager.should_save(101) is True
