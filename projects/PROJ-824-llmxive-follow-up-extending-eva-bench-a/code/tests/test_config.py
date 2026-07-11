"""
Tests for the configuration module, specifically focusing on FR-006 constraints.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    validate_environment,
    get_device,
    LATENCY_STEPS,
    ENV_CONSTRAINTS,
    ConfigurationError
)

class TestConfigModule:
    """Test suite for config.py"""

    def test_latency_steps_range(self):
        """Test that latency steps cover the required 200ms-2000ms range."""
        assert LATENCY_STEPS[0] == 200
        assert LATENCY_STEPS[-1] == 2000
        assert len(LATENCY_STEPS) == 10  # 200, 400, ..., 2000

    def test_device_returns_cpu(self):
        """Test that get_device always returns 'cpu'."""
        assert get_device() == "cpu"

    def test_env_constraints_dict(self):
        """Test that ENV_CONSTRAINTS has correct keys and values."""
        assert ENV_CONSTRAINTS["force_cpu"] is True
        assert ENV_CONSTRAINTS["allow_gpu"] is False
        assert ENV_CONSTRAINTS["allow_quantization"] is False

    @patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}, clear=False)
    def test_validate_environment_fails_with_gpu_visible(self):
        """Test that validate_environment raises error if GPU is visible."""
        # Ensure CUDA_VISIBLE_DEVICES is set to a non-empty, non-"-1" value
        with pytest.raises(RuntimeError) as exc_info:
            validate_environment()
        assert "FR-006 Violation" in str(exc_info.value)
        assert "GPU acceleration is prohibited" in str(exc_info.value)

    @patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "-1"}, clear=False)
    def test_validate_environment_passes_with_cpu_forced(self):
        """Test that validate_environment passes when GPU is disabled."""
        # This should not raise
        result = validate_environment()
        assert result is True

    @patch.dict(os.environ, {"FORCE_QUANTIZATION": "true"}, clear=False)
    def test_validate_environment_fails_with_quantization(self):
        """Test that validate_environment raises error if quantization is forced."""
        with pytest.raises(RuntimeError) as exc_info:
            validate_environment()
        assert "FR-006 Violation" in str(exc_info.value)
        assert "Model quantization is explicitly prohibited" in str(exc_info.value)

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_environment_passes_clean_env(self):
        """Test that validate_environment passes in a clean environment."""
        # Remove CUDA_VISIBLE_DEVICES if it exists in the real env
        if "CUDA_VISIBLE_DEVICES" in os.environ:
            del os.environ["CUDA_VISIBLE_DEVICES"]
        
        result = validate_environment()
        assert result is True