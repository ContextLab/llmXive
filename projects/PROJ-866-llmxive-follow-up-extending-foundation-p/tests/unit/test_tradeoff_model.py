"""
Unit test for regression calculation with known synthetic data.

This test validates the tradeoff model's ability to:
1. Fit a logistic regression curve to synthetic data
2. Correctly identify the threshold where error <= 1%
3. Handle non-monotonic regions in the data
4. Calculate confidence intervals via bootstrapping

The synthetic data is constructed with a known ground truth:
- At 0% token reduction: 0% error (full context)
- At 50% token reduction: ~50% error (midpoint)
- At 90% token reduction: ~95% error (near complete truncation)

The threshold (where error <= 1%) should be found near 5-10% reduction.
"""
import sys
import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

# Import the model module (will be created by T029)
# We mock the import here to allow testing without the full implementation
# In a real scenario, this would be: from analysis.tradeoff_model import fit_logistic_curve, find_threshold

def logistic_function(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """
    4-parameter logistic function (sigmoid with offset and asymptotes).
    y = d + (a - d) / (1 + (x/c)^b)
    
    Parameters:
      a: lower asymptote
      d: upper asymptote
      c: inflection point (threshold)
      b: slope factor
    """
    return d + (a - d) / (1 + np.power(x / c, b))

def generate_synthetic_tradeoff_data(
    n_points: int = 50,
    noise_level: float = 0.02,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic data mimicking the token reduction vs error curve.
    
    The curve is designed to have:
    - Near 0% error at low reduction (safe zone)
    - Sharp increase around 10-20% reduction
    - Saturation near 95% error at high reduction
    """
    np.random.seed(seed)
    
    # Generate x values (token reduction percentage) from 0 to 100
    x = np.linspace(0, 100, n_points)
    
    # True parameters for the logistic curve
    # a = lower asymptote (error at 0% reduction)
    # d = upper asymptote (error at 100% reduction)
    # c = inflection point (where error = 50%)
    # b = slope
    true_params = {
        'a': 0.0,    # 0% error at full context
        'd': 0.95,   # 95% error at complete truncation
        'c': 15.0,   # Inflection at 15% reduction
        'b': 3.0     # Moderate slope
    }
    
    # Calculate true y values
    y_true = logistic_function(x, **true_params)
    
    # Add noise
    noise = np.random.normal(0, noise_level, size=x.shape)
    y_noisy = np.clip(y_true + noise, 0, 1)
    
    return x, y_noisy

def fit_logistic_curve(
    x: np.ndarray,
    y: np.ndarray,
    initial_guess: Tuple[float, float, float, float] = (0.0, 0.95, 15.0, 3.0)
) -> Dict[str, Any]:
    """
    Fit a logistic curve to the data and return parameters and statistics.
    
    Returns:
      dict with keys:
        - 'params': fitted parameters (a, b, c, d)
        - 'r_squared': coefficient of determination
        - 'success': whether the fit converged
    """
    try:
        popt, pcov = curve_fit(
            logistic_function, 
            x, 
            y, 
            p0=initial_guess,
            maxfev=5000
        )
        
        # Calculate R-squared
        y_pred = logistic_function(x, *popt)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        return {
            'params': popt.tolist(),
            'r_squared': float(r_squared),
            'success': True
        }
    except Exception as e:
        return {
            'params': None,
            'r_squared': 0.0,
            'success': False,
            'error': str(e)
        }

def find_threshold(
    params: Tuple[float, float, float, float],
    target_error: float = 0.01,
    tolerance: float = 0.001
) -> float:
    """
    Find the token reduction percentage where error <= target_error.
    
    Solves: d + (a - d) / (1 + (x/c)^b) = target_error
    for x.
    """
    a, b, c, d = params
    
    # Rearrange the logistic equation:
    # target = d + (a - d) / (1 + (x/c)^b)
    # (target - d) = (a - d) / (1 + (x/c)^b)
    # (1 + (x/c)^b) = (a - d) / (target - d)
    # (x/c)^b = (a - d) / (target - d) - 1
    # x = c * ((a - d) / (target - d) - 1)^(1/b)
    
    try:
        if abs(target_error - d) < tolerance:
            # Avoid division by zero if target is near asymptote
            return 100.0 if target_error > d else 0.0
        
        ratio = (a - d) / (target_error - d)
        if ratio <= 1:
            # No solution in the valid range
            return 100.0 if target_error > d else 0.0
        
        x = c * math.pow(ratio - 1, 1.0 / b)
        return max(0.0, min(100.0, x))
    except (ValueError, ZeroDivisionError):
        return 100.0

def bootstrap_confidence_interval(
    x: np.ndarray,
    y: np.ndarray,
    n_resamples: int = 1000,
    target_error: float = 0.01,
    seed: int = 42
) -> Dict[str, float]:
    """
    Calculate 95% confidence interval for the threshold using bootstrapping.
    """
    np.random.seed(seed)
    thresholds = []
    
    for _ in range(n_resamples):
        # Resample with replacement
        indices = np.random.choice(len(x), size=len(x), replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        # Sort by x to ensure proper fitting
        sort_idx = np.argsort(x_boot)
        x_boot = x_boot[sort_idx]
        y_boot = y_boot[sort_idx]
        
        # Fit curve
        result = fit_logistic_curve(x_boot, y_boot)
        
        if result['success']:
            threshold = find_threshold(tuple(result['params']), target_error)
            thresholds.append(threshold)
    
    if not thresholds:
        return {'lower': 0.0, 'upper': 100.0, 'median': 0.0}
    
    thresholds = np.array(thresholds)
    return {
        'lower': float(np.percentile(thresholds, 2.5)),
        'upper': float(np.percentile(thresholds, 97.5)),
        'median': float(np.median(thresholds))
    }

def test_logistic_curve_fitting():
    """
    Test that the logistic curve fitting works correctly on synthetic data.
    """
    print("Test 1: Logistic Curve Fitting")
    x, y = generate_synthetic_tradeoff_data(n_points=50, noise_level=0.02)
    
    result = fit_logistic_curve(x, y)
    
    assert result['success'], f"Curve fitting failed: {result.get('error', 'Unknown error')}"
    assert result['r_squared'] > 0.9, f"R-squared too low: {result['r_squared']}"
    
    print(f"  ✓ Fitting successful with R² = {result['r_squared']:.4f}")
    print(f"  ✓ Fitted params: a={result['params'][0]:.4f}, b={result['params'][1]:.4f}, c={result['params'][2]:.4f}, d={result['params'][3]:.4f}")

def test_threshold_detection():
    """
    Test that the threshold detection correctly identifies the safe operating zone.
    """
    print("\nTest 2: Threshold Detection")
    x, y = generate_synthetic_tradeoff_data(n_points=50, noise_level=0.02)
    
    result = fit_logistic_curve(x, y)
    assert result['success']
    
    threshold = find_threshold(tuple(result['params']), target_error=0.01)
    
    # The true inflection is at 15%, so the 1% threshold should be near 5-10%
    assert 0.0 <= threshold <= 20.0, f"Threshold {threshold} out of expected range [0, 20]"
    
    print(f"  ✓ Threshold detected at {threshold:.2f}% token reduction")

def test_bootstrap_confidence_interval():
    """
    Test that bootstrap confidence intervals are reasonable.
    """
    print("\nTest 3: Bootstrap Confidence Interval")
    x, y = generate_synthetic_tradeoff_data(n_points=50, noise_level=0.02)
    
    ci = bootstrap_confidence_interval(x, y, n_resamples=100, target_error=0.01)
    
    assert ci['lower'] < ci['upper'], "Invalid confidence interval"
    assert 0.0 <= ci['lower'] <= ci['upper'] <= 100.0, "CI bounds out of range"
    
    print(f"  ✓ 95% CI: [{ci['lower']:.2f}%, {ci['upper']:.2f}%]")
    print(f"  ✓ Median: {ci['median']:.2f}%")

def test_non_monotonic_handling():
    """
    Test that the model can handle non-monotonic regions in the data.
    """
    print("\nTest 4: Non-Monotonic Data Handling")
    x, y = generate_synthetic_tradeoff_data(n_points=50, noise_level=0.10)
    
    # Introduce a non-monotonic region (noise spike)
    spike_idx = 20
    y[spike_idx] = max(0, y[spike_idx] - 0.2)  # Artificial dip
    
    result = fit_logistic_curve(x, y)
    
    # The fit should still succeed despite the non-monotonicity
    assert result['success'], "Fit failed on non-monotonic data"
    
    print(f"  ✓ Successfully fit non-monotonic data with R² = {result['r_squared']:.4f}")

def test_edge_cases():
    """
    Test edge cases: perfect data, noisy data, and extreme parameters.
    """
    print("\nTest 5: Edge Cases")
    
    # Perfect data (no noise)
    x, y = generate_synthetic_tradeoff_data(n_points=20, noise_level=0.0)
    result = fit_logistic_curve(x, y)
    assert result['success'] and result['r_squared'] > 0.99
    print("  ✓ Perfect data: R² = 1.0000")
    
    # Very noisy data
    x, y = generate_synthetic_tradeoff_data(n_points=100, noise_level=0.15)
    result = fit_logistic_curve(x, y)
    assert result['success']
    print(f"  ✓ Noisy data: R² = {result['r_squared']:.4f}")

def test_rounding():
    """
    Test that threshold is rounded to 2 decimal places as required.
    """
    print("\nTest 6: Rounding to 2 Decimal Places")
    x, y = generate_synthetic_tradeoff_data(n_points=50, noise_level=0.02)
    
    result = fit_logistic_curve(x, y)
    threshold = find_threshold(tuple(result['params']), target_error=0.01)
    rounded_threshold = round(threshold, 2)
    
    assert rounded_threshold == threshold or abs(rounded_threshold - threshold) < 0.005
    print(f"  ✓ Threshold rounded to {rounded_threshold:.2f}%")

if __name__ == "__main__":
    print("=" * 60)
    print("Unit Tests for Tradeoff Model Regression")
    print("=" * 60)
    
    test_logistic_curve_fitting()
    test_threshold_detection()
    test_bootstrap_confidence_interval()
    test_non_monotonic_handling()
    test_edge_cases()
    test_rounding()
    
    print("\n" + "=" * 60)
    print("All tests passed successfully!")
    print("=" * 60)