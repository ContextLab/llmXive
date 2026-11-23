"""
Unit tests for the Demographic Parity Difference formula.

This module verifies the correctness of the demographic parity difference
calculation as implemented in code/utils/metrics.py.

Demographic Parity Difference is defined as:
DP_Diff = P(Y_hat=1 | A=1) - P(Y_hat=1 | A=0)

Where:
  Y_hat = predicted outcome
  A     = protected attribute (binary)

A value of 0 indicates perfect demographic parity.
"""

import pytest
import numpy as np
import pandas as pd
from utils.metrics import demographic_parity_difference


class TestDemographicParityDifference:
    """Unit tests for demographic_parity_difference function."""

    def test_perfect_parity(self):
        """Test case where demographic parity is perfectly satisfied."""
        # Equal positive rates for both groups
        y_pred = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        protected = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        # P(Y_hat=1|A=1) = 2/4 = 0.5
        # P(Y_hat=1|A=0) = 2/4 = 0.5
        # Difference = 0.0
        assert np.isclose(result, 0.0), f"Expected 0.0, got {result}"

    def test_complete_separation_group_1_higher(self):
        """Test case where group 1 has 100% positive rate, group 0 has 0%."""
        y_pred = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        protected = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        # P(Y_hat=1|A=1) = 4/4 = 1.0
        # P(Y_hat=1|A=0) = 0/4 = 0.0
        # Difference = 1.0
        assert np.isclose(result, 1.0), f"Expected 1.0, got {result}"

    def test_complete_separation_group_0_higher(self):
        """Test case where group 0 has 100% positive rate, group 1 has 0%."""
        y_pred = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        protected = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        # P(Y_hat=1|A=1) = 0/4 = 0.0
        # P(Y_hat=1|A=0) = 4/4 = 1.0
        # Difference = -1.0
        assert np.isclose(result, -1.0), f"Expected -1.0, got {result}"

    def test_partial_parity_imbalance(self):
        """Test case with partial imbalance between groups."""
        y_pred = np.array([1, 1, 0, 0, 1, 0, 0, 0])
        protected = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        # P(Y_hat=1|A=1) = 2/4 = 0.5
        # P(Y_hat=1|A=0) = 1/4 = 0.25
        # Difference = 0.25
        assert np.isclose(result, 0.25), f"Expected 0.25, got {result}"

    def test_unbalanced_group_sizes(self):
        """Test with unequal group sizes."""
        y_pred = np.array([1, 1, 1, 1, 1, 0, 0])
        protected = np.array([1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        # P(Y_hat=1|A=1) = 3/3 = 1.0
        # P(Y_hat=1|A=0) = 2/4 = 0.5
        # Difference = 0.5
        assert np.isclose(result, 0.5), f"Expected 0.5, got {result}"

    def test_pandas_input(self):
        """Test that pandas Series inputs are handled correctly."""
        y_pred = pd.Series([1, 0, 1, 0, 1, 0, 1, 0])
        protected = pd.Series([1, 1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        assert np.isclose(result, 0.0), f"Expected 0.0 for pandas input, got {result}"

    def test_list_input(self):
        """Test that list inputs are handled correctly."""
        y_pred = [1, 0, 1, 0, 1, 0, 1, 0]
        protected = [1, 1, 1, 1, 0, 0, 0, 0]
        
        result = demographic_parity_difference(y_pred, protected)
        
        assert np.isclose(result, 0.0), f"Expected 0.0 for list input, got {result}"

    def test_single_group_raises_error(self):
        """Test that input with only one protected group raises an error."""
        y_pred = np.array([1, 0, 1, 0])
        protected = np.array([1, 1, 1, 1])
        
        with pytest.raises(ValueError, match="Both protected groups must be present"):
            demographic_parity_difference(y_pred, protected)

    def test_empty_input_raises_error(self):
        """Test that empty input raises an error."""
        y_pred = np.array([])
        protected = np.array([])
        
        with pytest.raises(ValueError, match="Input arrays cannot be empty"):
            demographic_parity_difference(y_pred, protected)

    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched array lengths raise an error."""
        y_pred = np.array([1, 0, 1])
        protected = np.array([1, 1])
        
        with pytest.raises(ValueError, match="Input arrays must have the same length"):
            demographic_parity_difference(y_pred, protected)

    def test_non_binary_protected_attribute(self):
        """Test that non-binary protected attributes are handled (or raise)."""
        # The function should ideally handle or reject non-binary protected attributes.
        # Based on the formula, it expects binary (0/1).
        y_pred = np.array([1, 0, 1, 0, 1, 0])
        protected = np.array([1, 2, 1, 2, 1, 2])
        
        # This should raise an error because 2 is not a valid binary value (0 or 1)
        # or the implementation might treat it as group 1 (non-zero).
        # We test for the expected behavior: either it raises or computes correctly
        # if it treats non-zero as 1.
        # Assuming strict binary check:
        with pytest.raises(ValueError, match="Protected attribute must be binary"):
            demographic_parity_difference(y_pred, protected)

    def test_non_binary_predictions(self):
        """Test that non-binary predictions raise an error."""
        y_pred = np.array([0, 1, 2, 0, 1, 0])
        protected = np.array([1, 1, 1, 0, 0, 0])
        
        with pytest.raises(ValueError, match="Predictions must be binary"):
            demographic_parity_difference(y_pred, protected)

    def test_large_dataset(self):
        """Test with a larger synthetic dataset."""
        np.random.seed(42)
        n = 10000
        y_pred = np.random.randint(0, 2, n)
        protected = np.random.randint(0, 2, n)
        
        result = demographic_parity_difference(y_pred, protected)
        
        # With random data, result should be close to 0 but not exactly 0
        # Just verify it's a float and within [-1, 1]
        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0

    def test_all_zeros_predictions(self):
        """Test when all predictions are 0."""
        y_pred = np.array([0, 0, 0, 0, 0, 0, 0, 0])
        protected = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        # P(Y_hat=1|A=1) = 0
        # P(Y_hat=1|A=0) = 0
        assert np.isclose(result, 0.0)

    def test_all_ones_predictions(self):
        """Test when all predictions are 1."""
        y_pred = np.array([1, 1, 1, 1, 1, 1, 1, 1])
        protected = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        
        result = demographic_parity_difference(y_pred, protected)
        
        # P(Y_hat=1|A=1) = 1
        # P(Y_hat=1|A=0) = 1
        assert np.isclose(result, 0.0)