"""
Contract test for statistical test input validation.

Verifies that the statistical utility functions correctly validate
paired vectors before performing the Wilcoxon signed-rank test.

This test ensures:
1. Inputs must be paired (same length).
2. Inputs must be numeric sequences.
3. Inputs must not be empty.
4. Inputs must contain at least 3 pairs for statistical validity.
"""
import os
import sys
import pytest
from pathlib import Path
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.statistics.wilcoxon_test import validate_paired_inputs, run_wilcoxon_signed_rank


class TestStatUtilsInputValidation:
    """Test suite for statistical input validation logic."""

    def test_valid_paired_vectors(self):
        """Test that valid paired vectors pass validation."""
        group_a = [0.8, 0.9, 0.85, 0.92, 0.88]
        group_b = [0.7, 0.75, 0.8, 0.82, 0.79]
        
        # Should not raise an exception
        result = validate_paired_inputs(group_a, group_b)
        assert result is True
        
        # Also verify with numpy arrays
        arr_a = np.array(group_a)
        arr_b = np.array(group_b)
        result_np = validate_paired_inputs(arr_a, arr_b)
        assert result_np is True

    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched vector lengths raise ValueError."""
        group_a = [0.8, 0.9, 0.85]
        group_b = [0.7, 0.75]  # Different length
        
        with pytest.raises(ValueError) as excinfo:
            validate_paired_inputs(group_a, group_b)
        
        assert "length" in str(excinfo.value).lower()

    def test_empty_vectors_raises_error(self):
        """Test that empty vectors raise ValueError."""
        group_a = []
        group_b = []
        
        with pytest.raises(ValueError) as excinfo:
            validate_paired_inputs(group_a, group_b)
        
        assert "empty" in str(excinfo.value).lower()

    def test_non_numeric_inputs_raises_error(self):
        """Test that non-numeric inputs raise ValueError or TypeError."""
        group_a = [0.8, 0.9, "invalid"]
        group_b = [0.7, 0.75, 0.8]
        
        with pytest.raises((ValueError, TypeError)):
            validate_paired_inputs(group_a, group_b)

    def test_too_few_samples_raises_error(self):
        """Test that fewer than 3 pairs raises ValueError."""
        group_a = [0.8, 0.9]
        group_b = [0.7, 0.75]
        
        with pytest.raises(ValueError) as excinfo:
            validate_paired_inputs(group_a, group_b)
        
        assert "minimum" in str(excinfo.value).lower() or "3" in str(excinfo.value)

    def test_run_wilcoxon_with_valid_input(self):
        """Test that Wilcoxon test runs successfully with valid input."""
        # Simulating success rates from 5 seeds
        group_a = [0.85, 0.90, 0.82, 0.88, 0.91]  # Cross-embodiment
        group_b = [0.75, 0.80, 0.78, 0.82, 0.79]  # Baseline
        
        result = run_wilcoxon_signed_rank(group_a, group_b)
        
        assert "statistic" in result
        assert "p_value" in result
        assert isinstance(result["statistic"], (int, float))
        assert isinstance(result["p_value"], float)
        assert 0 <= result["p_value"] <= 1

    def test_run_wilcoxon_with_identical_inputs(self):
        """Test that identical inputs result in p-value of 1.0."""
        group = [0.85, 0.90, 0.82, 0.88, 0.91]
        
        result = run_wilcoxon_signed_rank(group, group)
        
        # If groups are identical, the statistic should be 0 and p-value 1.0
        assert result["statistic"] == 0
        assert result["p_value"] == 1.0

    def test_run_wilcoxon_with_very_small_p_value(self):
        """Test that large differences result in small p-value."""
        # Create groups with a very clear difference
        group_a = [0.95, 0.96, 0.97, 0.98, 0.99]
        group_b = [0.50, 0.51, 0.52, 0.53, 0.54]
        
        result = run_wilcoxon_signed_rank(group_a, group_b)
        
        # We expect a very small p-value given the large difference
        assert result["p_value"] < 0.05