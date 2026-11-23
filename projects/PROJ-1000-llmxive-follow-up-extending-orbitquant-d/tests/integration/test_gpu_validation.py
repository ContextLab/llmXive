"""
Integration tests for GPU Validation (T046).

Tests the logic of run_gpu_validation.py without requiring actual GPU hardware.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We cannot import run_gpu_validation directly if it fails on import due to missing GPU,
# so we mock the heavy dependencies.
# However, since the script uses standard imports and conditional logic, we can test the flow.

@pytest.fixture
def mock_config():
    """Mock Config to avoid file system dependencies."""
    with patch('code.run_gpu_validation.CONFIG') as mock_cfg:
        yield mock_cfg

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state"
        state_path.mkdir()
        yield state_path

def test_gpu_unavailable_triggers_offload(temp_state_dir):
    """Test that missing GPU triggers offload logic."""
    from code.run_gpu_validation import load_log, save_log, run_validation
    
    # Mock dependencies
    with patch('code.run_gpu_validation.check_gpu_availability', return_value=False), \
         patch('code.run_gpu_validation.get_offload_command', return_value="mock_cmd"), \
         patch('code.run_gpu_validation.trigger_offload_log'), \
         patch('code.run_gpu_validation.LOG_FILE', temp_state_dir / "gpu_validation_log.json"):
        
        run_validation()
        
        log_path = temp_state_dir / "gpu_validation_log.json"
        assert log_path.exists()
        
        with open(log_path, "r") as f:
            log_data = json.load(f)
        
        assert log_data["final_status"] == "offload_triggered"
        assert len(log_data["attempts"]) == 1
        assert log_data["attempts"][0]["success"] is False

def test_gpu_available_load_fails(temp_state_dir):
    """Test that available GPU but load failure is recorded."""
    from code.run_gpu_validation import run_validation
    
    with patch('code.run_gpu_validation.check_gpu_availability', return_value=True), \
         patch('code.run_gpu_validation.ModelLoader') as mock_loader_cls, \
         patch('code.run_gpu_validation.LOG_FILE', temp_state_dir / "gpu_validation_log.json"):
        
        # Mock loader to raise an error
        mock_loader = MagicMock()
        mock_loader.load_model.side_effect = RuntimeError("CUDA OOM")
        mock_loader_cls.return_value = mock_loader
        
        run_validation()
        
        log_path = temp_state_dir / "gpu_validation_log.json"
        assert log_path.exists()
        
        with open(log_path, "r") as f:
            log_data = json.load(f)
        
        assert log_data["final_status"] == "failed"
        assert log_data["attempts"][-1]["success"] is False
        assert "CUDA OOM" in log_data["attempts"][-1]["error"]

def test_gpu_available_load_succeeds(temp_state_dir):
    """Test that successful load is recorded."""
    from code.run_gpu_validation import run_validation
    import torch
    
    with patch('code.run_gpu_validation.check_gpu_availability', return_value=True), \
         patch('code.run_gpu_validation.ModelLoader') as mock_loader_cls, \
         patch('code.run_gpu_validation.LOG_FILE', temp_state_dir / "gpu_validation_log.json"):
        
        # Mock a successful model
        mock_model = MagicMock()
        mock_param = MagicMock()
        mock_param.device.type = "cuda"
        mock_model.parameters.return_value = iter([mock_param])
        
        mock_loader = MagicMock()
        mock_loader.load_model.return_value = mock_model
        mock_loader_cls.return_value = mock_loader
        
        # Mock torch.cuda.is_available to return True inside attempt_load_flux
        with patch('torch.cuda.is_available', return_value=True):
            run_validation()
        
        log_path = temp_state_dir / "gpu_validation_log.json"
        assert log_path.exists()
        
        with open(log_path, "r") as f:
            log_data = json.load(f)
        
        assert log_data["final_status"] == "success"
        assert log_data["model"] == "flux.1-dev"
        assert log_data["device"] == "cuda"
        assert log_data["attempts"][-1]["success"] is True
