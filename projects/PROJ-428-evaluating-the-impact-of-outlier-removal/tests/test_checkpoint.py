import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.checkpoint import (
    MONTE_CARLO_REPLICATES,
    load_checkpoint,
    save_checkpoint,
    get_replicate_count,
    update_checkpoint,
    finalize_checkpoint,
    reset_checkpoint,
    _get_state_dir,
    _checkpoint_path
)
from src.setup_dirs import setup_directories

@pytest.fixture
def mock_state_dir():
    """Create a temporary directory to act as the state directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the setup_directories function to return our temp dir
        mock_dirs = {"state": Path(tmpdir)}
        with patch('src.checkpoint.setup_directories', return_value=mock_dirs):
            yield Path(tmpdir)

def test_save_and_load_checkpoint(mock_state_dir):
    data = {"completed_replicates": 50, "status": "running"}
    save_checkpoint(data)
    
    loaded = load_checkpoint()
    assert loaded == data
    assert (mock_state_dir / "checkpoint.json").exists()

def test_load_checkpoint_no_file(mock_state_dir):
    assert load_checkpoint() is None

def test_get_replicate_count_new_run(mock_state_dir):
    # No checkpoint exists
    count = get_replicate_count()
    assert count == MONTE_CARLO_REPLICATES

def test_get_replicate_count_resumed(mock_state_dir):
    # Simulate a checkpoint with 40 completed
    save_checkpoint({"completed_replicates": 40, "status": "running"})
    count = get_replicate_count()
    assert count == MONTE_CARLO_REPLICATES - 40

def test_get_replicate_count_exceeds_limit(mock_state_dir):
    # Simulate a checkpoint that somehow exceeds the limit
    save_checkpoint({"completed_replicates": MONTE_CARLO_REPLICATES + 10})
    with pytest.raises(RuntimeError, match="exceeds the constitutional limit"):
        get_replicate_count()

def test_update_checkpoint_within_limit(mock_state_dir):
    update_checkpoint(50)
    loaded = load_checkpoint()
    assert loaded["completed_replicates"] == 50

def test_update_checkpoint_exceeds_limit(mock_state_dir, caplog):
    with pytest.raises(RuntimeError, match="exceeding the constitutional limit"):
        update_checkpoint(MONTE_CARLO_REPLICATES + 1)
    
    # Verify critical log was written
    assert any("CRITICAL" in record.message for record in caplog.records)

def test_finalize_checkpoint(mock_state_dir):
    finalize_checkpoint()
    loaded = load_checkpoint()
    assert loaded["completed_replicates"] == MONTE_CARLO_REPLICATES
    assert loaded["status"] == "completed"

def test_reset_checkpoint(mock_state_dir):
    save_checkpoint({"completed_replicates": 10})
    reset_checkpoint()
    assert not (_checkpoint_path()).exists()
    assert load_checkpoint() is None

def test_reset_checkpoint_no_file(mock_state_dir):
    # Should not raise
    reset_checkpoint()