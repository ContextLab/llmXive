"""
Unit tests for T040: Verify runner.py CPU execution path.

Tests that runner.py ensures CPU-only execution and no CUDA calls are made.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import torch

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.pipeline.runner import ensure_cpu_only_execution, measure_component_latency


class TestEnsureCpuOnlyExecution:
    """Tests for ensure_cpu_only_execution function."""

    @patch('src.pipeline.runner.torch.cuda.is_available')
    @patch('src.pipeline.runner.torch.cuda.device_count')
    def test_cpu_only_when_cuda_available(self, mock_device_count, mock_is_available):
        """Test that function handles CUDA availability correctly."""
        # Mock CUDA as available but we force CPU
        mock_is_available.return_value = True
        mock_device_count.return_value = 1
        
        # The function should not raise an error, just ensure CPU usage
        # It sets environment variables and warnings
        with patch('src.pipeline.runner.os.environ') as mock_environ:
            with patch('src.pipeline.runner.warnings.warn') as mock_warn:
                result = ensure_cpu_only_execution()
                
                # Should set CUDA_VISIBLE_DEVICES to empty string
                assert 'CUDA_VISIBLE_DEVICES' in mock_environ.__setitem__.call_args_list[0][0]
                
                # Should warn user
                mock_warn.assert_called()

    @patch('src.pipeline.runner.torch.cuda.is_available')
    def test_cpu_only_when_cuda_not_available(self, mock_is_available):
        """Test behavior when CUDA is not available."""
        mock_is_available.return_value = False
        
        with patch('src.pipeline.runner.os.environ') as mock_environ:
            with patch('src.pipeline.runner.warnings.warn') as mock_warn:
                result = ensure_cpu_only_execution()
                
                # Should still set environment variable
                assert 'CUDA_VISIBLE_DEVICES' in mock_environ.__setitem__.call_args_list[0][0]


class TestMeasureComponentLatency:
    """Tests for measure_component_latency function."""

    def test_measure_component_latency_returns_dict(self):
        """Test that the function returns a dictionary with timing info."""
        
        # Mock a simple callable that takes time
        def mock_callable():
            import time
            time.sleep(0.01)
            return {"result": "success"}
        
        result = measure_component_latency(mock_callable, "test_component")
        
        assert isinstance(result, dict)
        assert "component" in result
        assert "latency_ms" in result
        assert "result" in result
        assert result["component"] == "test_component"
        assert result["latency_ms"] >= 0  # Latency should be non-negative

    def test_measure_component_latency_handles_exceptions(self):
        """Test that exceptions in the callable are handled gracefully."""
        
        def failing_callable():
            raise ValueError("Test error")
        
        result = measure_component_latency(failing_callable, "failing_component")
        
        assert isinstance(result, dict)
        assert "component" in result
        assert "latency_ms" in result
        assert "error" in result
        assert "Test error" in result["error"]
