"""
Unit tests for Benjamini-Hochberg FDR correction implementation.

This module tests the `benjamini_hochberg` function which is expected to be
implemented in `code/feature_analysis.py`. The tests verify:
1. Correct sorting and ranking of p-values.
2. Correct calculation of critical values.
3. Correct identification of significant features based on the FDR threshold.
4. Handling of edge cases (e.g., all p-values significant, none significant).
"""

import pytest
import numpy as np
import pandas as pd

# Import the function to be tested.
# We expect this function to exist in code/feature_analysis.py.
# If it doesn't exist yet, this test file will fail to import, which is expected
# before the implementation task (T042) is complete.
try:
    from code.feature_analysis import benjamini_hochberg
except ImportError:
    # If the module or function doesn't exist, we define a placeholder to allow
    # the test structure to be validated, but the tests will fail as expected.
    # In a real run, this import error would cause pytest to fail.
    benjamini_hochberg = None


@pytest.fixture
def sample_p_values():
    """Provide a set of sample p-values for testing."""
    # Simulate p-values from a correlation analysis of 10 features
    return [0.001, 0.015, 0.025, 0.04, 0.06, 0.12, 0.18, 0.25, 0.35, 0.5]


@pytest.fixture
def feature_names():
    """Provide corresponding feature names."""
    return [f"feature_{i}" for i in range(10)]


@pytest.fixture
def expected_bh_results():
    """
    Expected results for the sample p-values at q=0.05.
    Calculated manually:
    Sorted p-values: [0.001, 0.015, 0.025, 0.04, 0.06, 0.12, 0.18, 0.25, 0.35, 0.5]
    Ranks (i):      [1,    2,    3,    4,   5,   6,   7,   8,   9,   10]
    Critical val:   [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.036, 0.04, 0.045, 0.05]
    Comparison:     [T,    T,    T,    F,   F,   F,   F,   F,   F,   F]
    (Note: BH procedure finds the largest k where p(k) <= (k/m)*q, then rejects all <= k)
    Here:
    0.001 <= 0.005 (True)
    0.015 <= 0.010 (False) -> Stop? No, BH finds max k.
    Let's re-calculate carefully:
    m = 10, q = 0.05
    i=1: 0.001 <= 0.05 * 1/10 = 0.005 -> True
    i=2: 0.015 <= 0.05 * 2/10 = 0.010 -> False
    i=3: 0.025 <= 0.05 * 3/10 = 0.015 -> False
    ...
    Actually, the standard BH procedure is:
    1. Sort p-values.
    2. Find the largest k such that p(k) <= (k/m) * q.
    3. Reject all hypotheses for i <= k.

    Let's re-evaluate:
    i=1: 0.001 <= 0.005 (True)
    i=2: 0.015 <= 0.010 (False)
    i=3: 0.025 <= 0.015 (False)
    i=4: 0.040 <= 0.020 (False)
    i=5: 0.060 <= 0.025 (False)
    i=6: 0.120 <= 0.030 (False)
    i=7: 0.180 <= 0.035 (False)
    i=8: 0.250 <= 0.040 (False)
    i=9: 0.350 <= 0.045 (False)
    i=10: 0.500 <= 0.050 (False)

    Wait, my manual calculation for i=2 is 0.015 <= 0.010 which is False.
    So k=1 is the largest index where condition holds?
    Let's check i=1 again: 0.001 <= 0.005. True.
    So k=1.
    Therefore, only the first feature (p=0.001) should be rejected.

    Let's try a different set of p-values where more are rejected.
    Maybe the example p-values in the fixture are too high.
    Let's adjust the fixture or the expected result based on the actual logic.
    Standard BH:
    p_sorted = [0.001, 0.015, 0.025, 0.04, 0.06, 0.12, 0.18, 0.25, 0.35, 0.5]
    critical = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.036, 0.04, 0.045, 0.05]
    Comparison:
    0.001 <= 0.005 (True)
    0.015 <= 0.010 (False)
    So only 1 rejection.

    Let's create a fixture with more obvious rejections.
    """
    pass


@pytest.fixture
def sample_p_values_2():
    """Provide a set of sample p-values where multiple rejections are expected."""
    # m=5, q=0.05
    # p = [0.001, 0.004, 0.009, 0.02, 0.06]
    # critical = [0.01, 0.02, 0.03, 0.04, 0.05]
    # 0.001 <= 0.01 (T)
    # 0.004 <= 0.02 (T)
    # 0.009 <= 0.03 (T)
    # 0.02  <= 0.04 (T)
    # 0.06  <= 0.05 (F)
    # Max k = 4. Rejections: 4.
    return [0.001, 0.004, 0.009, 0.02, 0.06]


@pytest.fixture
def feature_names_2():
    return ["f1", "f2", "f3", "f4", "f5"]


def test_bh_import():
    """Test that the benjamini_hochberg function can be imported."""
    assert benjamini_hochberg is not None, "benjamini_hochberg function not found in code/feature_analysis.py"


def test_bh_returns_dataframe(sample_p_values_2, feature_names_2):
    """Test that the function returns a pandas DataFrame."""
    p_values = sample_p_values_2
    names = feature_names_2
    result = benjamini_hochberg(p_values, names, q=0.05)
    assert isinstance(result, pd.DataFrame), "Function should return a DataFrame"


def test_bh_columns(sample_p_values_2, feature_names_2):
    """Test that the DataFrame contains the required columns."""
    p_values = sample_p_values_2
    names = feature_names_2
    result = benjamini_hochberg(p_values, names, q=0.05)
    required_columns = ['feature', 'p_value', 'rank', 'critical_value', 'is_significant']
    assert all(col in result.columns for col in required_columns), f"Missing columns: {set(required_columns) - set(result.columns)}"


def test_bh_rejection_count(sample_p_values_2, feature_names_2):
    """Test that the correct number of hypotheses are rejected."""
    p_values = sample_p_values_2
    names = feature_names_2
    result = benjamini_hochberg(p_values, names, q=0.05)
    # Based on manual calculation: 4 rejections expected
    expected_rejections = 4
    actual_rejections = result['is_significant'].sum()
    assert actual_rejections == expected_rejections, f"Expected {expected_rejections} rejections, got {actual_rejections}"


def test_bh_order_preserved(sample_p_values_2, feature_names_2):
    """Test that the output preserves the original order of features (or is sorted by p-value as expected)."""
    # The function should typically return sorted by p-value for the calculation,
    # but the 'feature' column should map back correctly.
    # Let's assume the output is sorted by p-value (ascending) as per standard BH procedure.
    p_values = sample_p_values_2
    names = feature_names_2
    result = benjamini_hochberg(p_values, names, q=0.05)
    
    # Check if p_values are sorted ascending
    assert result['p_value'].is_monotonic_increasing, "Output should be sorted by p-value ascending"
    
    # Check if the features corresponding to the sorted p-values are correct
    sorted_p = sorted(p_values)
    assert list(result['p_value']) == sorted_p, "P-values in result do not match sorted input"


def test_bh_all_significant():
    """Test case where all p-values are below the threshold."""
    p_values = [0.001, 0.002, 0.003]
    names = ["a", "b", "c"]
    result = benjamini_hochberg(p_values, names, q=0.05)
    assert result['is_significant'].all(), "All features should be significant"


def test_bh_none_significant():
    """Test case where no p-values are significant."""
    p_values = [0.5, 0.6, 0.7]
    names = ["a", "b", "c"]
    result = benjamini_hochberg(p_values, names, q=0.05)
    assert not result['is_significant'].any(), "No features should be significant"


def test_bh_single_feature():
    """Test case with a single feature."""
    p_values = [0.01]
    names = ["single"]
    result = benjamini_hochberg(p_values, names, q=0.05)
    assert len(result) == 1
    assert result.iloc[0]['is_significant'] == True # 0.01 <= 0.05 * 1/1 = 0.05


def test_bh_empty_input():
    """Test case with empty input."""
    p_values = []
    names = []
    with pytest.raises(ValueError):
        benjamini_hochberg(p_values, names, q=0.05)
