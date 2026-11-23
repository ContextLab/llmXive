"""
Unit tests for T029g: compare_slopes logic.
"""
import json
import math
import os
import tempfile
from pathlib import Path
import sys
import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.compare_slopes import (
    load_scaling_logs, 
    perform_log_log_regression, 
    determine_complexity_class_from_slope,
    RegressionResult
)

def test_perform_log_log_regression_linear():
    """Test regression with a perfect linear relationship (O(n))."""
    # y = 2x -> log(y) = log(2) + log(x) -> slope should be 1.0
    # Let's generate data: n=[10, 100, 1000], t=[20, 200, 2000]
    data = [
        {"n": 10, "duration": 20},
        {"n": 100, "duration": 200},
        {"n": 1000, "duration": 2000}
    ]
    
    result = perform_log_log_regression(data)
    
    # Slope should be very close to 1.0
    assert abs(result.slope - 1.0) < 0.01, f"Expected slope ~1.0, got {result.slope}"
    assert result.r_squared > 0.99
    assert result.n_samples == 3

def test_perform_log_log_regression_quadratic():
    """Test regression with a quadratic relationship (O(n^2))."""
    # y = x^2 -> log(y) = 2*log(x) -> slope should be 2.0
    data = [
        {"n": 10, "duration": 100},
        {"n": 100, "duration": 10000},
        {"n": 1000, "duration": 1000000}
    ]
    
    result = perform_log_log_regression(data)
    
    assert abs(result.slope - 2.0) < 0.01, f"Expected slope ~2.0, got {result.slope}"
    assert result.r_squared > 0.99

def test_determine_complexity_class_unknown():
    """Test that low R^2 returns UNKNOWN."""
    assert determine_complexity_class_from_slope(1.5, 0.5) == "UNKNOWN (Low R^2)"

def test_determine_complexity_class_linear():
    """Test linear classification."""
    assert determine_complexity_class_from_slope(1.0, 0.95) == "O(n)"

def test_determine_complexity_class_quadratic():
    """Test quadratic classification."""
    assert determine_complexity_class_from_slope(2.0, 0.95) == "O(n^2) or O(n^3)"

def test_load_scaling_logs_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_scaling_logs("/nonexistent/path.json")

def test_load_scaling_logs_invalid_format():
    """Test that invalid JSON format raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"not": "a list"}')
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_scaling_logs(temp_path)
    finally:
        os.unlink(temp_path)