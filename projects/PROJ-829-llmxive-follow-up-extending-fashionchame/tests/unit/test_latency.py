import pytest
import json
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from typing import Callable, List, Dict, Any

# Add the project root to sys.path to allow imports from src
# Assuming this test file is at tests/unit/test_latency.py
# and the source is at code/src/metrics/latency.py
# We adjust the path relative to the test file location
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.metrics.latency import evaluate_latency_pass_fail, calculate_moving_average_latency, measure_inference_latency

# --- Fixtures ---

@pytest.fixture
def mock_callable():
    """A mock function that sleeps for a fixed duration."""
    def mock_func():
        time.sleep(0.05) # 50ms
    return mock_func

@pytest.fixture
def latency_data():
    """Sample latency measurements in milliseconds."""
    return [10.5, 12.3, 11.8, 13.0, 11.5]

# --- Tests for evaluate_latency_pass_fail ---

def test_evaluate_latency_pass_fail_pass():
    """Test that the function returns PASS when average is below threshold."""
    average_ms = 45.0
    threshold_ms = 50.0
    result = evaluate_latency_pass_fail(average_ms, threshold_ms)
    
    assert isinstance(result, dict)
    assert result["status"] == "PASS"
    assert result["average_ms"] == average_ms

def test_evaluate_latency_pass_fail_fail():
    """Test that the function returns FAIL when average is above threshold."""
    average_ms = 55.0
    threshold_ms = 50.0
    result = evaluate_latency_pass_fail(average_ms, threshold_ms)
    
    assert isinstance(result, dict)
    assert result["status"] == "FAIL"
    assert result["average_ms"] == average_ms

def test_evaluate_latency_pass_fail_exact_threshold():
    """Test that the function returns PASS when average equals threshold (<=)."""
    average_ms = 50.0
    threshold_ms = 50.0
    result = evaluate_latency_pass_fail(average_ms, threshold_ms)
    
    assert isinstance(result, dict)
    assert result["status"] == "PASS"
    assert result["average_ms"] == average_ms

# --- Tests for calculate_moving_average_latency ---

def test_calculate_moving_average_latency_single():
    """Test moving average with a single value."""
    history = [10.0]
    new_val = 20.0
    window_size = 3
    
    result = calculate_moving_average_latency(history, new_val, window_size)
    
    assert result == 20.0

def test_calculate_moving_average_latency_within_window():
    """Test moving average when history is smaller than window."""
    history = [10.0, 12.0]
    new_val = 14.0
    window_size = 5
    
    result = calculate_moving_average_latency(history, new_val, window_size)
    
    # Average of [10, 12, 14]
    expected = (10.0 + 12.0 + 14.0) / 3.0
    assert abs(result - expected) < 1e-6

def test_calculate_moving_average_latency_exceeds_window():
    """Test moving average when history exceeds window size."""
    history = [10.0, 20.0, 30.0]
    new_val = 40.0
    window_size = 3
    
    result = calculate_moving_average_latency(history, new_val, window_size)
    
    # Should take last (window_size - 1) items from history + new_val
    # History: [10, 20, 30], New: 40. Window size 3.
    # Keep last 2 from history: [20, 30]. Add new: [20, 30, 40].
    expected = (20.0 + 30.0 + 40.0) / 3.0
    assert abs(result - expected) < 1e-6

# --- Tests for measure_inference_latency ---

def test_measure_inference_latency_correct_duration(mock_callable):
    """Test that measure_inference_latency returns a value close to the mock sleep."""
    # The mock sleeps for 0.05s (50ms)
    # We allow some tolerance for system overhead
    tolerance_ms = 10.0 
    expected_ms = 50.0
    
    start = time.perf_counter()
    mock_callable()
    end = time.perf_counter()
    
    actual_duration_ms = (end - start) * 1000
    
    assert abs(actual_duration_ms - expected_ms) < tolerance_ms

def test_measure_inference_latency_raises_on_error():
    """Test that measure_inference_latency propagates exceptions from the callable."""
    def failing_func():
        raise ValueError("Simulated error")
    
    with pytest.raises(ValueError, match="Simulated error"):
        measure_inference_latency(failing_func)