import numpy as np
import pytest
from code.modeling.stats_utils import bonferroni_correction, benjamini_hochberg_correction

def test_bonferroni_basic():
    """Test basic Bonferroni correction logic."""
    # 3 tests with p-values [0.01, 0.05, 0.10]
    # Expected: [0.03, 0.15, 0.30] (capped at 1.0)
    p_values = [0.01, 0.05, 0.10]
    corrected = bonferroni_correction(p_values)
    
    expected = np.array([0.03, 0.15, 0.30])
    np.testing.assert_array_almost_equal(corrected, expected, decimal=5)

def test_bonferroni_capping():
    """Test that Bonferroni correction caps values at 1.0."""
    p_values = [0.5, 0.8, 0.9]
    corrected = bonferroni_correction(p_values)
    
    # 0.5 * 3 = 1.5 -> 1.0
    # 0.8 * 3 = 2.4 -> 1.0
    # 0.9 * 3 = 2.7 -> 1.0
    expected = np.array([1.0, 1.0, 1.0])
    np.testing.assert_array_almost_equal(corrected, expected, decimal=5)

def test_bonferroni_empty():
    """Test handling of empty input."""
    p_values = []
    corrected = bonferroni_correction(p_values)
    assert len(corrected) == 0

def test_benjamini_hochberg_basic():
    """Test basic BH correction logic."""
    # 3 tests with p-values [0.01, 0.05, 0.10]
    # Sorted: same order
    # Ranks: 1, 2, 3
    # Raw adjusted: [0.01*3/1, 0.05*3/2, 0.10*3/3] = [0.03, 0.075, 0.10]
    # Monotonicity check: 0.03 <= 0.075 <= 0.10 (already monotonic)
    p_values = [0.01, 0.05, 0.10]
    corrected = benjamini_hochberg_correction(p_values)
    
    # Expected: [0.03, 0.075, 0.10]
    expected = np.array([0.03, 0.075, 0.10])
    np.testing.assert_array_almost_equal(corrected, expected, decimal=5)

def test_benjamini_hochberg_monotonicity():
    """Test that BH enforces monotonicity."""
    # Create a case where raw adjustment would violate monotonicity
    # p-values: [0.05, 0.02] -> sorted: [0.02, 0.05]
    # Ranks: 1, 2
    # Raw: [0.02*2/1, 0.05*2/2] = [0.04, 0.05]
    # This is already monotonic. Let's try [0.05, 0.01] -> sorted [0.01, 0.05]
    # Raw: [0.01*2, 0.05*1] = [0.02, 0.05] (monotonic)
    # Let's try a case where it matters: [0.1, 0.01] -> sorted [0.01, 0.1]
    # Raw: [0.01*2, 0.1*1] = [0.02, 0.10] (monotonic)
    # Actually, BH raw is (m/i)*p_i. Since p_i is increasing and 1/i is decreasing,
    # it's not guaranteed to be monotonic.
    # Example: p = [0.04, 0.05, 0.06] with m=3
    # Ranks: 1, 2, 3
    # Raw: [0.04*3, 0.05*1.5, 0.06*1] = [0.12, 0.075, 0.06]
    # This is decreasing! We need to enforce q_i <= q_{i+1} backwards.
    # So q_3 = 0.06, q_2 = min(0.075, 0.06) = 0.06, q_1 = min(0.12, 0.06) = 0.06
    # Result: [0.06, 0.06, 0.06]
    
    p_values = [0.04, 0.05, 0.06]
    corrected = benjamini_hochberg_correction(p_values)
    
    # All should be 0.06 due to monotonicity enforcement
    expected = np.array([0.06, 0.06, 0.06])
    np.testing.assert_array_almost_equal(corrected, expected, decimal=5)

def test_benjamini_hochberg_empty():
    """Test handling of empty input."""
    p_values = []
    corrected = benjamini_hochberg_correction(p_values)
    assert len(corrected) == 0

def test_bonferroni_numpy_array():
    """Test Bonferroni with numpy array input."""
    p_values = np.array([0.01, 0.05, 0.10])
    corrected = bonferroni_correction(p_values)
    assert isinstance(corrected, np.ndarray)
    assert len(corrected) == 3

def test_benjamini_hochberg_numpy_array():
    """Test BH with numpy array input."""
    p_values = np.array([0.01, 0.05, 0.10])
    corrected = benjamini_hochberg_correction(p_values)
    assert isinstance(corrected, np.ndarray)
    assert len(corrected) == 3

def test_bonferroni_pandas_series():
    """Test Bonferroni with pandas Series input."""
    p_values = pd.Series([0.01, 0.05, 0.10])
    corrected = bonferroni_correction(p_values)
    assert isinstance(corrected, np.ndarray)
    assert len(corrected) == 3

def test_benjamini_hochberg_pandas_series():
    """Test BH with pandas Series input."""
    p_values = pd.Series([0.01, 0.05, 0.10])
    corrected = benjamini_hochberg_correction(p_values)
    assert isinstance(corrected, np.ndarray)
    assert len(corrected) == 3