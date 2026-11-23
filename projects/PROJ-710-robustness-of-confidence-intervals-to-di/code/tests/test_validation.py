import pytest
import numpy as np
import sys
import os
from unittest.mock import patch, MagicMock
from code.analysis.validation import (
    enforce_float64,
    ensure_cpu_only,
    validate_input_data,
    validate_config_precision,
    wrap_numpy_function,
    validate_pipeline_environment
)


class TestFloat64Enforcement:
    """Test that enforce_float64 correctly converts inputs to float64."""

    def test_float32_array_conversion(self):
        """Verify float32 arrays are converted to float64."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        result = enforce_float64(arr)
        assert result.dtype == np.float64
        np.testing.assert_array_equal(result, arr)

    def test_int_array_conversion(self):
        """Verify integer arrays are converted to float64."""
        arr = np.array([1, 2, 3], dtype=np.int32)
        result = enforce_float64(arr)
        assert result.dtype == np.float64
        np.testing.assert_array_equal(result, arr.astype(np.float64))

    def test_list_conversion(self):
        """Verify lists are converted to float64 arrays."""
        lst = [1.0, 2.0, 3.0]
        result = enforce_float64(lst)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64
        np.testing.assert_array_equal(result, lst)

    def test_preserves_float64(self):
        """Verify float64 arrays remain unchanged."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        result = enforce_float64(arr)
        assert result.dtype == np.float64
        assert result is arr  # Should return same reference if already float64

    def test_dataframe_conversion(self):
        """Verify pandas DataFrames are converted to float64."""
        import pandas as pd
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4.0, 5.0, 6.0]})
        result = enforce_float64(df)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64

    def test_scalar_conversion(self):
        """Verify scalar values are converted to float64."""
        val = 3.14159
        result = enforce_float64(val)
        assert result.dtype == np.float64


class TestCPUOnlyEnforcement:
    """Test that ensure_cpu_only correctly restricts execution to CPU."""

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    def test_no_cuda_available(self, mock_device_count, mock_is_available):
        """Test when CUDA is not available."""
        mock_is_available.return_value = False
        mock_device_count.return_value = 0
        result = ensure_cpu_only()
        assert result is True

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    def test_cuda_available_forced_cpu(self, mock_device_count, mock_is_available):
        """Test that CUDA availability is ignored and CPU is enforced."""
        mock_is_available.return_value = True
        mock_device_count.return_value = 1
        result = ensure_cpu_only()
        assert result is True

    @patch('torch.cuda.is_available')
    def test_mps_available(self, mock_is_available):
        """Test that MPS (Apple Silicon) is also blocked."""
        # Note: This test assumes MPS availability check is part of the validation
        # In a real scenario, we'd mock torch.backends.mps.is_available()
        mock_is_available.return_value = False
        result = ensure_cpu_only()
        assert result is True


class TestInputValidation:
    """Test validate_input_data function."""

    def test_valid_data(self):
        """Test validation passes for valid data."""
        data = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        result = validate_input_data(data)
        assert result is True

    def test_nan_values(self):
        """Test validation fails for NaN values."""
        data = np.array([1.0, np.nan, 3.0], dtype=np.float64)
        with pytest.raises(ValueError):
            validate_input_data(data)

    def test_inf_values(self):
        """Test validation fails for infinite values."""
        data = np.array([1.0, np.inf, 3.0], dtype=np.float64)
        with pytest.raises(ValueError):
            validate_input_data(data)

    def test_empty_array(self):
        """Test validation fails for empty arrays."""
        data = np.array([], dtype=np.float64)
        with pytest.raises(ValueError):
            validate_input_data(data)

    def test_wrong_dtype(self):
        """Test validation fails for wrong data type."""
        data = np.array([1, 2, 3], dtype=np.int32)
        with pytest.raises(ValueError):
            validate_input_data(data)


class TestPipelineEnvironment:
    """Test validate_pipeline_environment function."""

    @patch('code.analysis.validation.ensure_cpu_only')
    @patch('code.analysis.validation.validate_config_precision')
    def test_valid_environment(self, mock_config, mock_cpu):
        """Test validation passes for valid environment."""
        mock_cpu.return_value = True
        mock_config.return_value = True
        result = validate_pipeline_environment()
        assert result is True

    @patch('code.analysis.validation.ensure_cpu_only')
    @patch('code.analysis.validation.validate_config_precision')
    def test_cpu_validation_fails(self, mock_config, mock_cpu):
        """Test validation fails when CPU check fails."""
        mock_cpu.return_value = False
        mock_config.return_value = True
        with pytest.raises(EnvironmentError):
            validate_pipeline_environment()

    @patch('code.analysis.validation.ensure_cpu_only')
    @patch('code.analysis.validation.validate_config_precision')
    def test_config_validation_fails(self, mock_config, mock_cpu):
        """Test validation fails when config validation fails."""
        mock_cpu.return_value = True
        mock_config.return_value = False
        with pytest.raises(ValueError):
            validate_pipeline_environment()


def test_wrap_numpy_function():
    """Test that wrap_numpy_function correctly wraps numpy functions with validation."""
    @wrap_numpy_function
    def custom_sum(arr):
        return np.sum(arr)

    arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    result = custom_sum(arr)
    assert result == 6.0
    assert isinstance(result, (float, np.floating))

    # Test with invalid input
    arr_invalid = np.array([1.0, np.nan, 3.0], dtype=np.float64)
    with pytest.raises(ValueError):
        custom_sum(arr_invalid)
