"""
Unit tests for the feasibility estimator (code/utils/feasibility.py).

These tests verify that the MAX_SAMPLES calculation logic correctly
identifies bottlenecks and respects resource constraints.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.feasibility import estimate_feasibility, save_feasibility_report, MEMORY_LIMIT_GB, TIME_LIMIT_SECONDS

def test_estimate_feasibility_returns_valid_dict():
    """Verify that estimate_feasibility returns a dictionary with required keys."""
    result = estimate_feasibility()
    
    assert isinstance(result, dict)
    required_keys = [
        "max_samples", "constraint_bottleneck", 
        "estimated_memory_per_sample_gb", "estimated_time_per_sample_seconds",
        "memory_limit_gb", "time_limit_seconds"
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

def test_max_samples_is_integer_and_positive():
    """Verify that max_samples is a positive integer."""
    result = estimate_feasibility()
    assert isinstance(result["max_samples"], int)
    assert result["max_samples"] > 0

def test_bottleneck_logic_memory():
    """
    Verify bottleneck detection when memory is the limiting factor.
    We mock the constants to force memory to be the bottleneck.
    """
    # Force memory limit to be very low (e.g., allows only 2 samples)
    # while time allows many more (e.g., 100 samples)
    with patch('utils.feasibility.MEMORY_LIMIT_GB', 3.0), \
         patch('utils.feasibility.ESTIMATED_MEMORY_PER_SAMPLE_GB', 1.5), \
         patch('utils.feasibility.TIME_LIMIT_SECONDS', 3000), \
         patch('utils.feasibility.ESTIMATED_TIME_PER_SAMPLE_SECONDS', 10):
        
        result = estimate_feasibility()
        
        # Memory allows 3.0 / 1.5 = 2 samples
        # Time allows 3000 / 10 = 300 samples
        # Bottleneck should be memory
        assert result["max_samples"] == 2
        assert result["constraint_bottleneck"] == "memory"
        assert result["max_samples_by_memory"] == 2
        assert result["max_samples_by_time"] == 300

def test_bottleneck_logic_time():
    """
    Verify bottleneck detection when time is the limiting factor.
    """
    # Force time limit to be very low (e.g., allows 2 samples)
    # while memory allows many more (e.g., 100 samples)
    with patch('utils.feasibility.MEMORY_LIMIT_GB', 100.0), \
         patch('utils.feasibility.ESTIMATED_MEMORY_PER_SAMPLE_GB', 1.0), \
         patch('utils.feasibility.TIME_LIMIT_SECONDS', 30), \
         patch('utils.feasibility.ESTIMATED_TIME_PER_SAMPLE_SECONDS', 15):
        
        result = estimate_feasibility()
        
        # Memory allows 100 / 1.0 = 100 samples
        # Time allows 30 / 15 = 2 samples
        # Bottleneck should be time
        assert result["max_samples"] == 2
        assert result["constraint_bottleneck"] == "time"
        assert result["max_samples_by_memory"] == 100
        assert result["max_samples_by_time"] == 2

def test_save_feasibility_report_creates_json():
    """Verify that save_feasibility_report creates a valid JSON file."""
    result = estimate_feasibility()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_feasibility.json"
        
        saved_path = save_feasibility_report(result, output_path)
        
        assert saved_path.exists()
        
        with open(saved_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["max_samples"] == result["max_samples"]
        assert loaded_data["constraint_bottleneck"] == result["constraint_bottleneck"]

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
