import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code to path if not already present
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.hyperparams_logger import log_hyperparameters, get_current_memory_usage_gb

def test_log_hyperparameters_creates_file():
    """Test that log_hyperparameters creates the output file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_log.json"
        
        log_hyperparameters(
            run_id="test-1",
            hyperparameters={"lr": 0.001},
            memory_usage_gb=2.5,
            batch_size=8,
            dataset_capped=False,
            output_path=output_path
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["run_id"] == "test-1"
        assert data[0]["effective_batch_size"] == 8
        assert data[0]["dataset_capped"] is False
        assert "ram_threshold_gb" in data[0]
        assert data[0]["ram_threshold_gb"] == 6.0

def test_log_hyperparameters_appends():
    """Test that subsequent calls append to the existing log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_log.json"
        
        # First log
        log_hyperparameters(
            run_id="test-1",
            hyperparameters={"lr": 0.001},
            memory_usage_gb=2.5,
            batch_size=8,
            dataset_capped=False,
            output_path=output_path
        )
        
        # Second log
        log_hyperparameters(
            run_id="test-2",
            hyperparameters={"lr": 0.0001},
            memory_usage_gb=4.0,
            batch_size=4,
            dataset_capped=True,
            capped_size=500,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[0]["run_id"] == "test-1"
        assert data[1]["run_id"] == "test-2"
        assert data[1]["dataset_capped_size"] == 500

def test_get_current_memory_usage_gb():
    """Test that memory usage function returns a positive float."""
    mem = get_current_memory_usage_gb()
    assert isinstance(mem, float)
    assert mem >= 0.0