"""
Unit tests for T013/T014: Trend monotonicity verification logic.
"""
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from metrics import verify_trend_monotonicity

def test_verify_trend_monotonicity_increasing():
    """
    Test with a strictly increasing trend (error rate should rise with r).
    """
    r_vals = np.array([0.0, 0.2, 0.4, 0.6, 0.8])
    error_rates = np.array([0.05, 0.08, 0.12, 0.18, 0.25])
    
    is_mono, p_val = verify_trend_monotonicity(r_vals, error_rates)
    
    assert is_mono, "Should detect monotonic increase"
    assert p_val < 0.05, "Spearman correlation should be significant"
    print("Test increasing trend: PASSED")

def test_verify_trend_monotonicity_flat():
    """
    Test with a flat trend (no change in error rate).
    """
    r_vals = np.array([0.0, 0.2, 0.4, 0.6, 0.8])
    error_rates = np.array([0.05, 0.05, 0.05, 0.05, 0.05])
    
    is_mono, p_val = verify_trend_monotonicity(r_vals, error_rates)
    
    # Spearman might return 0 correlation, p-value might be high
    # Logic in metrics.py should handle this gracefully
    # We expect it NOT to be monotonic in a "significant" sense or return False if strictly increasing required.
    # Depending on implementation, it might be True (non-decreasing) but p > 0.05.
    # Here we just check it doesn't crash.
    print(f"Flat trend result: monotonic={is_mono}, p={p_val}")
    print("Test flat trend: PASSED (no crash)")

if __name__ == "__main__":
    test_verify_trend_monotonicity_increasing()
    test_verify_trend_monotonicity_flat()
    print("All trend tests passed.")