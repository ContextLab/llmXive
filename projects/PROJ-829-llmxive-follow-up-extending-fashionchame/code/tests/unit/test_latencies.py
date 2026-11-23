"""
Unit tests for T040: Latency measurement and thresholding.

Tests that latency.py correctly measures and evaluates inference times.
"""
import pytest
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.metrics.latency import (
    evaluate_latency_pass_fail,
    calculate_moving_average_latency,
    measure_inference_latency
)


class TestLatencyEvaluation:
    """Tests for latency pass/fail evaluation."""

    def test_evaluate_latency_pass_fail_returns_pass(self):
        """Test evaluation when latency is within threshold."""
        result = evaluate_latency_pass_fail(average_latency_ms=40.0, threshold_ms=50.0)
        
        assert result['status'] == 'PASS'
        assert result['average_ms'] == 40.0

    def test_evaluate_latency_pass_fail_returns_fail(self):
        """Test evaluation when latency exceeds threshold."""
        result = evaluate_latency_pass_fail(average_latency_ms=60.0, threshold_ms=50.0)
        
        assert result['status'] == 'FAIL'
        assert result['average_ms'] == 60.0

    def test_evaluate_latency_pass_fail_at_threshold(self):
        """Test evaluation when latency is exactly at threshold."""
        result = evaluate_latency_pass_fail(average_latency_ms=50.0, threshold_ms=50.0)
        
        # Should pass when exactly at threshold
        assert result['status'] == 'PASS'
        assert result['average_ms'] == 50.0

    def test_evaluate_latency_pass_fail_zero_latency(self):
        """Test evaluation with zero latency."""
        result = evaluate_latency_pass_fail(average_latency_ms=0.0, threshold_ms=50.0)
        
        assert result['status'] == 'PASS'
        assert result['average_ms'] == 0.0


class TestMovingAverage:
    """Tests for moving average latency calculation."""

    def test_calculate_moving_average_latency_basic(self):
        """Test basic moving average calculation."""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        moving_avg = calculate_moving_average_latency(latencies, window_size=3)
        
        assert isinstance(moving_avg, list)
        assert len(moving_avg) == len(latencies)
        
        # First two values should be partial averages
        assert moving_avg[0] == 10.0
        assert moving_avg[1] == 15.0  # (10+20)/2
        assert moving_avg[2] == 20.0  # (10+20+30)/3
        assert moving_avg[3] == 30.0  # (20+30+40)/3
        assert moving_avg[4] == 40.0  # (30+40+50)/3

    def test_calculate_moving_average_latency_window_equals_length(self):
        """Test when window size equals the list length."""
        latencies = [10.0, 20.0, 30.0]
        
        moving_avg = calculate_moving_average_latency(latencies, window_size=3)
        
        assert moving_avg[0] == 10.0
        assert moving_avg[1] == 15.0
        assert moving_avg[2] == 20.0  # Average of all three

    def test_calculate_moving_average_latency_empty_list(self):
        """Test with empty latency list."""
        moving_avg = calculate_moving_average_latency([], window_size=3)
        
        assert moving_avg == []

    def test_calculate_moving_average_latency_single_element(self):
        """Test with single element."""
        latencies = [25.0]
        
        moving_avg = calculate_moving_average_latency(latencies, window_size=3)
        
        assert moving_avg == [25.0]


class TestInferenceLatencyMeasurement:
    """Tests for actual latency measurement."""

    def test_measure_inference_latency_returns_positive_value(self):
        """Test that latency measurement returns a positive value."""
        def mock_callable():
            time.sleep(0.01)  # 10ms sleep
            return {"result": "success"}
        
        result = measure_inference_latency(mock_callable, "test_component")
        
        assert isinstance(result, dict)
        assert 'latency_ms' in result
        assert result['latency_ms'] >= 0
        assert result['component'] == 'test_component'

    def test_measure_inference_latency_approximate_timing(self):
        """Test that measured latency is approximately correct."""
        def mock_callable():
            time.sleep(0.05)  # 50ms sleep
            return {"result": "success"}
        
        result = measure_inference_latency(mock_callable, "test_timing")
        
        # Should be around 50ms, allow some tolerance
        assert 45 <= result['latency_ms'] <= 70

    def test_measure_inference_latency_handles_exceptions(self):
        """Test that exceptions in callable are handled."""
        def failing_callable():
            raise ValueError("Test error")
        
        result = measure_inference_latency(failing_callable, "failing_test")
        
        assert isinstance(result, dict)
        assert 'error' in result
        assert 'Test error' in result['error']
        assert result['latency_ms'] >= 0
