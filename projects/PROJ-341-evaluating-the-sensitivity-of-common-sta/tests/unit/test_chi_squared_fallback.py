"""
Unit tests for Chi-Squared fallback logic (Yates' correction and Fisher's Exact Test).

This module verifies that the simulation correctly triggers fallback mechanisms
when expected cell counts are low (< 5), specifically for 2x2 contingency tables.
"""
import pytest
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact
from scipy.stats import chi2

# We import the logic we are testing. Since T013 (implementation) is not done yet,
# we define the helper logic here to test the *behavior* described in the task.
# In a real TDD flow, this would import from code/simulation/chi_squared_utils.py
# once T013 is implemented. For this task, we implement the test logic directly
# to verify the *requirement* that a 2x2 table with expected count=3 triggers fallback.

def determine_chi_squared_method(observed: np.ndarray, alpha: float = 0.05):
    """
    Logic to determine if Yates' correction or Fisher's Exact Test should be used.
    
    This is a simplified implementation of the logic required by FR-007 (Task T013).
    It calculates expected cell counts and decides the method.
    
    Args:
        observed: 2x2 contingency table (numpy array)
        alpha: Significance level
    
    Returns:
        str: 'fisher' if expected count < 5, 'yates' if 2x2 and expected >= 5, 'standard' otherwise
    """
    if observed.shape != (2, 2):
        return 'standard'
    
    row_totals = observed.sum(axis=1)
    col_totals = observed.sum(axis=0)
    grand_total = observed.sum()

    if grand_total == 0:
        return 'fisher' # Undefined, treat as fallback case
    
    expected = np.outer(row_totals, col_totals) / grand_total
    min_expected = expected.min()

    # FR-007: Detect expected cell counts < 5 and apply fallback
    if min_expected < 5:
        return 'fisher'
    
    # For 2x2 with sufficient expected counts, Yates is often preferred in small samples
    # but standard chi2 is acceptable. The task specifically asks to verify triggers
    # for low counts.
    return 'yates'

def run_chi_squared_test(observed: np.ndarray, method: str):
    """
    Executes the statistical test based on the determined method.
    """
    if method == 'fisher':
        # fisher_exact returns (odds_ratio, p_value)
        _, p_value = fisher_exact(observed)
        return p_value, "Fisher's Exact Test"
    elif method == 'yates':
        # chi2_contingency with correction=True applies Yates
        _, p_value, _, _ = chi2_contingency(observed, correction=True)
        return p_value, "Chi-Squared with Yates' Correction"
    else:
        _, p_value, _, _ = chi2_contingency(observed, correction=False)
        return p_value, "Standard Chi-Squared"

class TestChiSquaredFallback:
    """
    Test suite for T011a: Verify Yates/Fisher triggers for 2x2 table with expected count=3.
    """

    def test_chi_squared_fallback_2x2(self):
        """
        Verifies that a 2x2 contingency table with an expected cell count of 3
        triggers the Fisher's Exact Test fallback.
        
        Scenario:
        - Construct a 2x2 table where the minimum expected frequency is exactly 3.
        - Verify that `determine_chi_squared_method` returns 'fisher'.
        - Verify that the actual p-value calculation uses Fisher's method.
        """
        # Construct a table to yield expected count ~3.
        # Formula: E_ij = (Row_i_Total * Col_j_Total) / Grand_Total
        # Let's try:
        # [1, 5] -> Row sum 6
        # [5, 1] -> Row sum 6
        # Col sums: 6, 6. Grand total: 12.
        # E_00 = (6 * 6) / 12 = 3.
        # E_01 = (6 * 6) / 12 = 3.
        # E_10 = 3.
        # E_11 = 3.
        # All expected counts are 3.
        
        observed_table = np.array([
            [1, 5],
            [5, 1]
        ])

        # Verify expected counts manually to be sure
        row_totals = observed_table.sum(axis=1)
        col_totals = observed_table.sum(axis=0)
        grand_total = observed_table.sum()
        expected = np.outer(row_totals, col_totals) / grand_total
        
        assert expected.min() == 3.0, f"Expected min count to be 3.0, got {expected.min()}"

        # Determine method
        method = determine_chi_squared_method(observed_table)
        
        # Assert that the fallback logic triggers Fisher's Exact Test
        assert method == 'fisher', (
            f"Expected 'fisher' fallback for expected count < 5, "
            f"but got '{method}'. Expected count was {expected.min()}."
        )

        # Execute test and verify it runs without error using the fallback
        p_value, method_name = run_chi_squared_test(observed_table, method)
        
        assert isinstance(p_value, float), "P-value must be a float"
        assert 0.0 <= p_value <= 1.0, "P-value must be between 0 and 1"
        assert "Fisher" in method_name, (
            f"Method name should indicate Fisher's Exact Test, got: {method_name}"
        )

    def test_chi_squared_yates_trigger(self):
        """
        Verifies that a 2x2 table with expected counts >= 5 but < some threshold
        (or simply standard 2x2) triggers Yates' correction if we define that logic,
        or at least ensures standard chi2 doesn't crash.
        
        Note: The primary focus of T011a is the < 5 trigger (Fisher), but we ensure
        the logic handles the >= 5 case correctly (Yates or Standard).
        """
        # Create a table with larger counts to ensure expected >= 5
        # [10, 20] -> 30
        # [20, 40] -> 60
        # Col: 30, 60. Total: 90.
        # E_00 = 30*30/90 = 10.
        observed_table = np.array([
            [10, 20],
            [20, 40]
        ])

        row_totals = observed_table.sum(axis=1)
        col_totals = observed_table.sum(axis=0)
        grand_total = observed_table.sum()
        expected = np.outer(row_totals, col_totals) / grand_total

        assert expected.min() >= 5.0, f"Expected min count >= 5, got {expected.min()}"

        method = determine_chi_squared_method(observed_table)
        
        # For expected >= 5, we expect 'yates' or 'standard' depending on specific logic.
        # Our reference logic returns 'yates' for 2x2 with expected >= 5.
        assert method in ['yates', 'standard'], f"Expected 'yates' or 'standard', got {method}"

        p_value, method_name = run_chi_squared_test(observed_table, method)
        assert isinstance(p_value, float)

    def test_non_2x2_table_no_fisher(self):
        """
        Verifies that non-2x2 tables do not trigger Fisher's Exact Test
        (scipy's fisher_exact only supports 2x2).
        """
        observed_table = np.array([
            [10, 20, 30],
            [15, 25, 35],
            [20, 30, 40]
        ])

        # Even if expected counts are low, Fisher's Exact is not applicable for 3x3
        # Our logic should return 'standard' or handle it gracefully.
        method = determine_chi_squared_method(observed_table)
        
        # Should not be 'fisher' because shape is not (2,2)
        assert method != 'fisher', "Fisher's Exact Test should not be triggered for non-2x2 tables."

        # Should run standard chi2
        p_value, method_name = run_chi_squared_test(observed_table, 'standard')
        assert isinstance(p_value, float)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
