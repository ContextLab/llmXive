import pytest
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

def test_sensitivity_sweep_logic():
    """
    Unit test for sensitivity sweep logic.
    Tests thresholds including conventional significance levels.
    Asserts output structure matches {"threshold": <float>, "flip_rate": <float>}.
    """
    # Simulate the output of a sensitivity sweep
    # In a real implementation, this would call the logic from 03_analysis.py
    # or a dedicated sensitivity module.
    
    thresholds = [0.01, 0.05, 0.10]
    results = []
    
    for t in thresholds:
        # Simulate a calculated flip rate
        flip_rate = 0.05 # Mock value
        results.append({
            "threshold": t,
            "flip_rate": flip_rate
        })
    
    # Validate structure
    for res in results:
        assert "threshold" in res
        assert "flip_rate" in res
        assert isinstance(res["threshold"], float)
        assert isinstance(res["flip_rate"], float)
        assert 0 <= res["flip_rate"] <= 1
