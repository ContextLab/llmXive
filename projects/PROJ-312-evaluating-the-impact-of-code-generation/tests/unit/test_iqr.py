"""
Unit tests for IQR outlier calculation logic.
Tests the calculation of Q1, Q3, IQR, and outlier bounds (Q1 - 1.5*IQR, Q3 + 1.5*IQR).
"""
import pytest
import numpy as np
from typing import List, Tuple

# Helper function to be tested (mirroring logic expected in code/analyze.py)
def calculate_iqr_bounds(values: List[float]) -> Tuple[float, float, float, float, float, float]:
    """
    Calculate IQR statistics and outlier bounds.
    
    Args:
        values: List of numerical values.
        
    Returns:
        Tuple of (q1, q3, iqr, lower_bound, upper_bound, is_outlier_mask)
        where is_outlier_mask is a list of booleans indicating if each value is an outlier.
    """
    if not values:
        return 0.0, 0.0, 0.0, 0.0, 0.0, []
        
    arr = np.array(values, dtype=float)
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    is_outlier = [(v < lower_bound or v > upper_bound) for v in arr]
    
    return q1, q3, iqr, lower_bound, upper_bound, is_outlier

class TestIQRCalculation:
    """Test suite for IQR outlier detection logic."""

    def test_basic_calculation(self):
        """Test basic IQR calculation with a known dataset."""
        # Dataset: 1, 2, 3, 4, 5, 6, 7, 8, 9
        # Q1 (25th percentile) = 2.5
        # Q3 (75th percentile) = 6.5
        # IQR = 4.0
        # Lower Bound = 2.5 - 6.0 = -3.5
        # Upper Bound = 6.5 + 6.0 = 12.5
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        q1, q3, iqr, lower, upper, outliers = calculate_iqr_bounds(data)
        
        assert q1 == 2.5
        assert q3 == 6.5
        assert iqr == 4.0
        assert lower == -3.5
        assert upper == 12.5
        assert not any(outliers)

    def test_outlier_detection(self):
        """Test that outliers are correctly identified."""
        # Dataset with clear outliers
        data = [10, 12, 12, 13, 12, 11, 15, 100, -50]
        # Sorted: -50, 10, 11, 12, 12, 12, 13, 15, 100
        # Q1 ~ 10.75, Q3 ~ 13.25, IQR ~ 2.5
        # Lower ~ 7.0, Upper ~ 17.0
        # -50 and 100 should be outliers
        
        q1, q3, iqr, lower, upper, outliers = calculate_iqr_bounds(data)
        
        # Verify bounds are calculated
        assert iqr > 0
        assert lower < upper
        
        # Check specific outlier flags
        # -50 is at index 8, 100 is at index 7 in original list
        assert outliers[0] == False  # 10
        assert outliers[7] == True   # 100
        assert outliers[8] == True   # -50

    def test_empty_list(self):
        """Test handling of empty input."""
        data = []
        q1, q3, iqr, lower, upper, outliers = calculate_iqr_bounds(data)
        
        assert q1 == 0.0
        assert q3 == 0.0
        assert iqr == 0.0
        assert lower == 0.0
        assert upper == 0.0
        assert outliers == []

    def test_single_value(self):
        """Test handling of a single value (IQR should be 0)."""
        data = [42.0]
        q1, q3, iqr, lower, upper, outliers = calculate_iqr_bounds(data)
        
        assert q1 == 42.0
        assert q3 == 42.0
        assert iqr == 0.0
        assert lower == 42.0
        assert upper == 42.0
        assert not any(outliers)

    def test_all_outliers(self):
        """Test a case where all values are outliers (impossible by definition, but test robustness)."""
        # With 3 values, IQR is 0 if 2 are same, or small. 
        # Let's try a case with extreme spread relative to count
        data = [1, 100, 1, 100, 1, 100]
        # Q1=1, Q3=100, IQR=99
        # Lower = 1 - 148.5 = -147.5
        # Upper = 100 + 148.5 = 248.5
        # No outliers expected here actually.
        
        # Let's try: 1, 2, 3, 4, 1000
        # Q1=1.75, Q3=3.25, IQR=1.5
        # Lower = 1.75 - 2.25 = -0.5
        # Upper = 3.25 + 2.25 = 5.5
        # 1000 is outlier
        data = [1, 2, 3, 4, 1000]
        q1, q3, iqr, lower, upper, outliers = calculate_iqr_bounds(data)
        
        assert outliers[4] == True
        assert not any(outliers[:4])

    def test_negative_values(self):
        """Test calculation with negative values."""
        data = [-10, -5, 0, 5, 10]
        # Q1 = -2.5, Q3 = 7.5, IQR = 10
        # Lower = -17.5, Upper = 22.5
        q1, q3, iqr, lower, upper, outliers = calculate_iqr_bounds(data)
        
        assert q1 == -2.5
        assert q3 == 7.5
        assert iqr == 10.0
        assert lower == -17.5
        assert upper == 22.5
        assert not any(outliers)

    def test_float_precision(self):
        """Test that float precision is handled correctly."""
        data = [1.1, 2.2, 3.3, 4.4, 5.5]
        q1, q3, iqr, lower, upper, outliers = calculate_iqr_bounds(data)
        
        assert isinstance(q1, float)
        assert isinstance(iqr, float)
        assert isinstance(lower, float)
        assert isinstance(upper, float)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])