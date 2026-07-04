"""
Tests for the validation module (T016).
Ensures double-precision enforcement and CPU-only constraints.
"""
import pytest
import numpy as np
import sys
import os
from unittest.mock import patch, MagicMock

# Add code directory to path if running directly
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from code.analysis.validation import (
    enforce_float64,
    ensure_cpu_only,
    validate_input_data,
    validate_pipeline_environment,
    FORCE_CPU_ONLY,
    FORCE_FLOAT64
)

class TestFloat64Enforcement:
    def test_convert_float32_to_float64(self):
        """Test that float32 arrays are converted to float64."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        result = enforce_float64(arr)
        assert result.dtype == np.float64
        np.testing.assert_array_almost_equal(result, arr)

    def test_convert_int_to_float64(self):
        """Test that integer arrays are converted to float64."""
        arr = np.array([1, 2, 3], dtype=np.int32)
        result = enforce_float64(arr)
        assert result.dtype == np.float64
        np.testing.assert_array_almost_equal(result, arr.astype(float))

    def test_already_float64_unchanged(self):
        """Test that float64 arrays are not modified unnecessarily."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        result = enforce_float64(arr)
        assert result.dtype == np.float64
        # Check if it's the same object or a copy (behavior may vary, but dtype must match)
        assert result is arr or np.array_equal(result, arr)

    def test_list_conversion(self):
        """Test that lists are converted to float64 arrays."""
        data = [1.0, 2.0, 3.0]
        result = enforce_float64(data)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64

    def test_complex_raises_error(self):
        """Test that complex arrays raise TypeError."""
        arr = np.array([1+2j, 3+4j])
        with pytest.raises(TypeError):
            enforce_float64(arr)

class TestCPUOnlyEnforcement:
    @patch('code.analysis.validation.torch')
    def test_cpu_only_passes_when_no_gpu(self, mock_torch):
        """Test that ensure_cpu_only passes when no GPU is available."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.mps.is_available.return_value = False
        # Should not raise
        ensure_cpu_only()

    @patch('code.analysis.validation.torch')
    def test_cpu_only_raises_when_gpu_available(self, mock_torch):
        """Test that ensure_cpu_only raises when GPU is detected."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.current_device.return_value = 0
        
        with pytest.raises(RuntimeError, match="GPU device is active"):
            ensure_cpu_only()

    @patch('code.analysis.validation.torch')
    def test_cpu_only_raises_when_mps_available(self, mock_torch):
        """Test that ensure_cpu_only raises when MPS is detected."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.mps.is_available.return_value = True
        
        with pytest.raises(RuntimeError, match="MPS"):
            ensure_cpu_only()

class TestInputValidation:
    def test_valid_float64_input(self):
        """Test validation passes for valid float64 input."""
        data = np.random.rand(10, 5).astype(np.float64)
        validate_input_data(data, "test_data")
        # If no exception, test passes

    def test_nan_input_raises(self):
        """Test that NaN values raise ValueError."""
        data = np.array([1.0, np.nan, 3.0], dtype=np.float64)
        with pytest.raises(ValueError, match="contains NaN"):
            validate_input_data(data, "test_data")

    def test_inf_input_raises(self):
        """Test that Inf values raise ValueError."""
        data = np.array([1.0, np.inf, 3.0], dtype=np.float64)
        with pytest.raises(ValueError, match="contains Inf"):
            validate_input_data(data, "test_data")

    def test_int_input_converted_and_validated(self):
        """Test that integer input is converted and validated."""
        data = np.array([1, 2, 3], dtype=np.int32)
        # Should convert to float64 and pass
        validate_input_data(data, "test_data")

class TestPipelineEnvironment:
    def test_validate_environment_returns_dict(self):
        """Test that validate_pipeline_environment returns a valid status dict."""
        result = validate_pipeline_environment()
        assert isinstance(result, dict)
        assert result["status"] == "PASS"
        assert result["cpu_only_enforced"] is True
        assert result["float64_enforced"] is True
        assert "numpy_version" in result
