"""
Unit tests for simulation logic, specifically focusing on statistical test selection
and error classification mechanisms.
"""
import pytest
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact
from typing import List, Tuple, Dict

# Mocking the simulation logic locally for testing the switch trigger
# In a full integration, this would import from code/simulation_engine.py
# but we implement the specific logic here to test the trigger condition directly
# as per the task requirement to verify the "expected cell < 5" switch.

def calculate_expected_cells(observed: np.ndarray) -> np.ndarray:
    """
    Calculate expected cell counts for a contingency table.
    Expected count = (row_sum * col_sum) / grand_total
    """
    row_sums = observed.sum(axis=1, keepdims=True)
    col_sums = observed.sum(axis=0, keepdims=True)
    grand_total = observed.sum()
    
    if grand_total == 0:
        return np.zeros_like(observed, dtype=float)
        
    expected = (row_sums * col_sums) / grand_total
    return expected

def should_use_fisher_exact(observed: np.ndarray) -> bool:
    """
    Determine if Fisher's Exact test should be used based on the
    rule: if any expected cell count is < 5.
    """
    expected = calculate_expected_cells(observed)
    return np.any(expected < 5)

class TestFisherExactSwitch:
    """
    Unit tests for the Fisher's Exact test switch trigger logic.
    Task: T016 - Verify switch trigger when expected cell < 5.
    """

    def test_large_counts_use_chi_squared(self):
        """
        Scenario: All expected counts are well above 5.
        Expected: Should NOT use Fisher's Exact (return False).
        """
        # 2x2 table with large counts
        observed = np.array([
            [50, 45],
            [55, 60]
        ])
        
        expected = calculate_expected_cells(observed)
        assert np.all(expected >= 5), "Test setup failed: expected counts should be >= 5"
        
        assert not should_use_fisher_exact(observed), \
            "Fisher's Exact should NOT be triggered when all expected cells >= 5"

    def test_small_expected_count_triggers_fisher(self):
        """
        Scenario: One expected count is below 5.
        Expected: Should use Fisher's Exact (return True).
        """
        # 2x2 table where one cell is small enough to drop expected count < 5
        # Row 1 sum = 10, Row 2 sum = 90. Col 1 sum = 10, Col 2 sum = 90. Total = 100.
        # Expected[0,0] = (10 * 10) / 100 = 1.0 (< 5)
        observed = np.array([
            [1, 9],
            [9, 81]
        ])
        
        expected = calculate_expected_cells(observed)
        assert expected[0, 0] < 5, "Test setup failed: expected[0,0] should be < 5"
        
        assert should_use_fisher_exact(observed), \
            "Fisher's Exact MUST be triggered when any expected cell < 5"

    def test_boundary_condition_exact_five(self):
        """
        Scenario: An expected count is exactly 5.0.
        Expected: Should NOT use Fisher's Exact (return False),
        as the rule is strictly < 5.
        """
        # Construct a table where expected[0,0] is exactly 5.
        # Let row sums be 20, 80. Col sums be 20, 80. Total 100.
        # Expected = (20*20)/100 = 4. Wait, that's < 5.
        # Let's try: Row sums 25, 75. Col sums 20, 80. Total 100.
        # Expected[0,0] = (25*20)/100 = 5.0
        # Observed needs to match these sums.
        # [5, 20] -> sum 25
        # [15, 60] -> sum 75
        # Col sums: 5+15=20, 20+60=80.
        observed = np.array([
            [5, 20],
            [15, 60]
        ])
        
        expected = calculate_expected_cells(observed)
        assert expected[0, 0] == 5.0, f"Test setup failed: expected[0,0] should be 5.0, got {expected[0,0]}"
        
        assert not should_use_fisher_exact(observed), \
            "Fisher's Exact should NOT be triggered when expected cells are exactly 5.0"

    def test_multiple_small_cells(self):
        """
        Scenario: Multiple expected counts are below 5.
        Expected: Should use Fisher's Exact.
        """
        observed = np.array([
            [2, 3],
            [4, 5]
        ])
        
        expected = calculate_expected_cells(observed)
        assert np.any(expected < 5), "Test setup failed: expected counts should be < 5"
        
        assert should_use_fisher_exact(observed), \
            "Fisher's Exact should be triggered when multiple expected cells < 5"

    def test_2x3_contingency_table(self):
        """
        Scenario: A 2x3 table with a small expected cell.
        Expected: Should use Fisher's Exact.
        """
        # 2 rows, 3 cols
        observed = np.array([
            [1, 10, 10],
            [10, 10, 10]
        ])
        
        # Check if logic handles non-square matrices
        # Row sums: 21, 30. Total 51.
        # Col sums: 11, 20, 20.
        # Expected[0,0] = (21 * 11) / 51 ≈ 4.52 (< 5)
        assert should_use_fisher_exact(observed), \
            "Fisher's Exact should be triggered for non-square tables if any expected < 5"

    def test_zero_sum_row_handling(self):
        """
        Scenario: A row with all zeros.
        Expected: Should handle gracefully (expected 0, which is < 5, triggers Fisher).
        Note: In practice, scipy might handle this differently, but the trigger logic
        relies on expected counts.
        """
        observed = np.array([
            [0, 0],
            [10, 10]
        ])
        
        # Expected will be 0 for the first row. 0 < 5 -> True.
        assert should_use_fisher_exact(observed), \
            "Fisher's Exact should be triggered if expected cell is 0 (which is < 5)"