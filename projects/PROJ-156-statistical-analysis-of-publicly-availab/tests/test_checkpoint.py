"""
Tests for the checkpoint utility.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Add the code/scripts path to sys.path to import utils
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code" / "scripts"))

from utils.checkpoint import save_checkpoint, load_checkpoint, delete_checkpoint, ensure_checkpoint_dir, CHECKPOINT_DIR

@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create a temporary checkpoint directory for testing."""
    # Monkeypatch the CHECKPOINT_DIR to use a temp directory
    original_dir = CHECKPOINT_DIR
    # We need to modify the module's reference if possible, or just test the logic
    # Since CHECKPOINT_DIR is a Path object in the module, we can't easily reassign it.
    # Instead, we will test the logic by creating a temp dir and ensuring functions work there.
    # For this specific test, we will rely on the fact that the functions create the dir if missing.
    # We'll use a specific filename to avoid collisions.
    return tmp_path

def test_save_and_load_checkpoint(temp_checkpoint_dir, monkeypatch):
    """Test saving and loading a checkpoint."""
    # Monkeypatch the module's CHECKPOINT_DIR to use our temp dir
    import utils.checkpoint as cp_module
    monkeypatch.setattr(cp_module, 'CHECKPOINT_DIR', temp_checkpoint_dir)
    monkeypatch.setattr(cp_module, 'BASE_DIR', temp_checkpoint_dir.parent)
    
    test_state = {
        "processed_games": ["game1", "game2"],
        "last_index": 5,
        "metadata": {"timestamp": "2023-10-27"}
    }
    filename = "test_state.json"
    
    # Save
    save_checkpoint(filename, test_state)
    
    # Verify file exists
    filepath = temp_checkpoint_dir / filename
    assert filepath.exists()
    
    # Load
    loaded_state = load_checkpoint(filename)
    assert loaded_state is not None
    assert loaded_state["processed_games"] == test_state["processed_games"]
    assert loaded_state["last_index"] == test_state["last_index"]

def test_load_nonexistent_checkpoint(temp_checkpoint_dir, monkeypatch):
    """Test loading a checkpoint that doesn't exist."""
    import utils.checkpoint as cp_module
    monkeypatch.setattr(cp_module, 'CHECKPOINT_DIR', temp_checkpoint_dir)
    
    result = load_checkpoint("nonexistent.json")
    assert result is None

def test_delete_checkpoint(temp_checkpoint_dir, monkeypatch):
    """Test deleting a checkpoint."""
    import utils.checkpoint as cp_module
    monkeypatch.setattr(cp_module, 'CHECKPOINT_DIR', temp_checkpoint_dir)
    
    filename = "to_delete.json"
    save_checkpoint(filename, {"data": "test"})
    
    assert (temp_checkpoint_dir / filename).exists()
    
    deleted = delete_checkpoint(filename)
    assert deleted
    assert not (temp_checkpoint_dir / filename).exists()

def test_delete_nonexistent_checkpoint(temp_checkpoint_dir, monkeypatch):
    """Test deleting a checkpoint that doesn't exist."""
    import utils.checkpoint as cp_module
    monkeypatch.setattr(cp_module, 'CHECKPOINT_DIR', temp_checkpoint_dir)
    
    deleted = delete_checkpoint("nonexistent.json")
    assert not deleted
