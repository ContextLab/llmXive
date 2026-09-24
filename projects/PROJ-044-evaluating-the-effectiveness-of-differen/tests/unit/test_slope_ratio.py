"""
Unit tests for T036: Slope Ratio Calculation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.slope_ratio import calculate_slope, calculate_slope_ratio_validation

def test_calculate_slope():
    """Test slope calculation with a known linear relationship."""
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([2.0, 4.0, 6.0, 8.0]) # y = 2x
    
    slope = calculate_slope(x, y)
    assert np.isclose(slope, 2.0), f"Expected slope 2.0, got {slope}"

def test_calculate_slope_negative():
    """Test slope calculation with negative relationship."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([10.0, 5.0, 0.0]) # y = -5x + 15
    
    slope = calculate_slope(x, y)
    assert np.isclose(slope, -5.0), f"Expected slope -5.0, got {slope}"

def test_slope_ratio_validation_pass():
    """
    Test the full validation logic with synthetic data where alpha=0.1
    is clearly steeper than alpha=1.0.
    """
    # Create synthetic data
    # Epsilon values: 0.5, 1.0, 2.0, 5.0
    # For alpha=0.1 (High Sensitivity): Accuracy drops sharply as epsilon decreases (noise increases)
    # Let's say: eps=5.0 -> acc=0.9, eps=2.0 -> acc=0.8, eps=1.0 -> acc=0.6, eps=0.5 -> acc=0.3
    # Slope approx: (0.3 - 0.9) / (0.5 - 5.0) = -0.6 / -4.5 = 0.13 (Wait, x is epsilon, y is accuracy)
    # x: [0.5, 1.0, 2.0, 5.0], y: [0.3, 0.6, 0.8, 0.9]
    # Slope = (0.9 - 0.3) / (5.0 - 0.5) = 0.6 / 4.5 = 0.133
    
    # Let's construct a clearer negative slope scenario (accuracy decreases as epsilon decreases)
    # x: [0.5, 1.0, 2.0, 5.0]
    # alpha=0.1 (Steep): [0.2, 0.4, 0.7, 0.9] -> Slope ~ (0.9-0.2)/(5-0.5) = 0.7/4.5 = 0.155
    # alpha=1.0 (Flat):  [0.85, 0.86, 0.87, 0.88] -> Slope ~ (0.88-0.85)/(5-0.5) = 0.03/4.5 = 0.0066
    
    # Ratio: 0.155 / 0.0066 = 23 > 2. Pass.
    
    data = []
    epsilons = [0.5, 1.0, 2.0, 5.0]
    
    # Alpha 0.1
    for eps in epsilons:
        acc = 0.15 + 0.15 * eps # Rough linear approximation
        data.append({'epsilon': eps, 'alpha': 0.1, 'global_accuracy': acc})
        
    # Alpha 1.0
    for eps in epsilons:
        acc = 0.85 + 0.005 * eps # Very flat
        data.append({'epsilon': eps, 'alpha': 1.0, 'global_accuracy': acc})
        
    df = pd.DataFrame(data)
    
    results = calculate_slope_ratio_validation(
        df, 
        epsilon_values=epsilons, 
        alpha_low=0.1, 
        alpha_high=1.0
    )
    
    assert results['pass_status'] is True, f"Expected PASS, got FAIL. Ratio: {results['ratio']}"
    assert results['slope_alpha_low'] > results['slope_alpha_high'], "Slope low should be steeper (more positive in this synthetic case)"
    
def test_slope_ratio_validation_fail():
    """
    Test validation logic where slopes are similar.
    """
    data = []
    epsilons = [0.5, 1.0, 2.0, 5.0]
    
    # Both alphas have similar slopes
    for eps in epsilons:
        data.append({'epsilon': eps, 'alpha': 0.1, 'global_accuracy': 0.1 + 0.1 * eps})
        data.append({'epsilon': eps, 'alpha': 1.0, 'global_accuracy': 0.2 + 0.1 * eps})
        
    df = pd.DataFrame(data)
    
    results = calculate_slope_ratio_validation(
        df, 
        epsilon_values=epsilons, 
        alpha_low=0.1, 
        alpha_high=1.0
    )
    
    assert results['pass_status'] is False, f"Expected FAIL, got PASS. Ratio: {results['ratio']}"

def test_insufficient_data():
    """Test that insufficient data points raise an error."""
    data = [
        {'epsilon': 1.0, 'alpha': 0.1, 'global_accuracy': 0.5},
        {'epsilon': 2.0, 'alpha': 0.1, 'global_accuracy': 0.6},
        # Only one point for alpha=1.0
        {'epsilon': 1.0, 'alpha': 1.0, 'global_accuracy': 0.8},
    ]
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Insufficient data points"):
        calculate_slope_ratio_validation(
            df, 
            epsilon_values=[1.0, 2.0], 
            alpha_low=0.1, 
            alpha_high=1.0
        )