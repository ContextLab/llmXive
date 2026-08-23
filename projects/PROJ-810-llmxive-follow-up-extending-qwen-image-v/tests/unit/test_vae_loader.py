"""
Unit tests for the VAE Loader module (CPU fallback logic).

This module tests the CPU-only loading constraints, memory feasibility checks,
and fallback protocols defined in `code/models/vae_loader.py`.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import torch
from unittest.mock import patch, MagicMock, PropertyMock

# Import the module under test
# Note: The import path assumes this test is run from the project root
# or that `code` is in the PYTHONPATH. The task specifies the file is at
# projects/PROJ-810-.../code/models/vae_loader.py
# We will import relative to the 'code' directory structure.
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
code_dir = project_root / "code"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from models.vae_loader import (
    check_model_availability,
    check_cpu_feasibility,
    trigger_model_substitution_protocol,
    load_vae_cpu,
    run_model_availability_check,
    MODEL_NAME,
    MEMORY_THRESHOLD_GB
)


class TestModelAvailability:
    """Tests for check_model_availability function."""

    @patch('models.vae_loader.AutoConfig')
    def test_model_accessible(self, mock_auto_config):
        """Test that a reachable model returns True."""
        mock_config = MagicMock()
        mock_auto_config.from_pretrained.return_value = mock_config
        
        is_available, message = check_model_availability()
        
        assert is_available is True
        assert "Model configuration accessible" in message
        mock_auto_config.from_pretrained.assert_called_once_with(
            MODEL_NAME, 
            trust_remote_code=True
        )

    @patch('models.vae_loader.AutoConfig')
    def test_model_access_failed(self, mock_auto_config):
        """Test that a failed download returns False."""
        mock_auto_config.from_pretrained.side_effect = Exception("Connection timeout")
        
        is_available, message = check_model_availability()
        
        assert is_available is False
        assert "Model access failed" in message


class TestCpuFeasibility:
    """Tests for check_cpu_feasibility function."""

    def test_model_within_memory_limits(self):
        """Test that a small model passes the memory check."""
        # The function uses a hardcoded estimate of 0.8B params -> ~3GB
        # which is < 7GB threshold.
        is_feasible, estimated_gb, message = check_cpu_feasibility()
        
        assert is_feasible is True
        assert estimated_gb > 0
        assert "within CPU memory limits" in message
        assert estimated_gb <= MEMORY_THRESHOLD_GB

    def test_memory_threshold_constant(self):
        """Verify the memory threshold is set correctly."""
        assert MEMORY_THRESHOLD_GB == 7.0


class TestFallbackProtocol:
    """Tests for trigger_model_substitution_protocol function."""

    def test_fallback_structure(self):
        """Test that the fallback protocol returns the correct structure."""
        reason = "Memory exceeded"
        result = trigger_model_substitution_protocol(reason)
        
        assert result["status"] == "FALLBACK_TRIGGERED"
        assert result["reason"] == reason
        assert "action" in result
        assert "Reduce sample size" in result["action"] or "switch to smaller model" in result["action"]

    def test_fallback_reason_persistence(self):
        """Test that the specific reason is preserved."""
        custom_reason = "Specific error: OOM on CPU"
        result = trigger_model_substitution_protocol(custom_reason)
        
        assert result["reason"] == custom_reason


class TestRunAvailabilityCheck:
    """Tests for the full availability check suite."""

    @patch('models.vae_loader.check_model_availability')
    @patch('models.vae_loader.check_cpu_feasibility')
    def test_full_pass_scenario(self, mock_feas, mock_avail):
        """Test the scenario where both checks pass."""
        mock_avail.return_value = (True, "Model OK")
        mock_feas.return_value = (True, 3.0, "Memory OK")
        
        result = run_model_availability_check()
        
        assert result["status"] == "PASS"
        assert result["availability"] is True
        assert result["cpu_feasibility"] is True
        assert "fallback" not in result

    @patch('models.vae_loader.check_model_availability')
    @patch('models.vae_loader.check_cpu_feasibility')
    def test_full_fail_feasibility_scenario(self, mock_feas, mock_avail):
        """Test the scenario where model is available but memory fails."""
        mock_avail.return_value = (True, "Model OK")
        mock_feas.return_value = (False, 8.0, "Memory Too High")
        
        result = run_model_availability_check()
        
        assert result["status"] == "FAIL"
        assert result["availability"] is True
        assert result["cpu_feasibility"] is False
        assert "fallback" in result
        assert result["fallback"]["status"] == "FALLBACK_TRIGGERED"

    @patch('models.vae_loader.check_model_availability')
    @patch('models.vae_loader.check_cpu_feasibility')
    def test_full_fail_availability_scenario(self, mock_feas, mock_avail):
        """Test the scenario where model is not available."""
        mock_avail.return_value = (False, "Network Error")
        mock_feas.return_value = (True, 3.0, "Memory OK")
        
        result = run_model_availability_check()
        
        assert result["status"] == "FAIL"
        assert result["availability"] is False
        # Feasibility might still be calculated or not, but status is FAIL
        assert result["availability_message"] == "Network Error"


class TestLoadVaeCpu:
    """Tests for load_vae_cpu function."""

    @patch('models.vae_loader.AutoModel')
    @patch('models.vae_loader.torch.cuda.is_available')
    def test_load_forces_cpu_device_map(self, mock_cuda, mock_auto_model):
        """Test that the model is loaded with device_map='cpu'."""
        mock_cuda.return_value = False
        
        mock_model = MagicMock()
        mock_model.device.type = 'cpu'
        mock_model.eval.return_value = mock_model
        mock_auto_model.from_pretrained.return_value = mock_model
        
        model = load_vae_cpu()
        
        # Verify from_pretrained was called with device_map="cpu"
        call_args = mock_auto_model.from_pretrained.call_args
        assert call_args.kwargs.get("device_map") == "cpu"
        assert call_args.kwargs.get("torch_dtype") == torch.float32
        assert call_args.kwargs.get("trust_remote_code") is True
        
        # Verify eval was called
        mock_model.eval.assert_called_once()

    @patch('models.vae_loader.AutoModel')
    @patch('models.vae_loader.torch.cuda.is_available')
    def test_load_handles_existing_gpu_model(self, mock_cuda, mock_auto_model):
        """Test that if model ends up on GPU (hypothetically), it is moved to CPU."""
        mock_cuda.return_value = True # GPU available but we ignore
        
        mock_model = MagicMock()
        # Simulate model initially on GPU
        type(mock_model).device = PropertyMock(return_value=MagicMock(type='cuda'))
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model
        mock_auto_model.from_pretrained.return_value = mock_model
        
        model = load_vae_cpu()
        
        # Verify .to('cpu') was called
        mock_model.to.assert_called_with('cpu')
        mock_model.eval.assert_called_once()

    @patch('models.vae_loader.AutoModel')
    def test_load_raises_on_failure(self, mock_auto_model):
        """Test that RuntimeError is raised if loading fails."""
        mock_auto_model.from_pretrained.side_effect = Exception("Download failed")
        
        with pytest.raises(RuntimeError) as exc_info:
            load_vae_cpu()
        
        assert "Failed to load VAE model on CPU" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])