import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling import calculate_permutation_pvalue

class TestPermutationPValue:
    """Tests for the calculate_permutation_pvalue function."""

    def test_calculate_pvalue_basic(self):
        """Test basic p-value calculation."""
        # Create mock permutation results
        np.random.seed(42)
        null_stats = np.random.normal(0, 1, 1000)
        
        permutation_results = pd.DataFrame({"statistic": null_stats})
        
        # Observed statistic that is extreme
        observed_stat = 3.0
        
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # Should be small since observed is extreme
        assert 0.0 <= p_value <= 1.0
        assert p_value < 0.1  # Should be small for extreme value
        
    def test_calculate_pvalue_extreme_observed(self):
        """Test p-value calculation with very extreme observed statistic."""
        null_stats = np.random.normal(0, 1, 10000)
        permutation_results = pd.DataFrame({"statistic": null_stats})
        
        # Very extreme observed statistic
        observed_stat = 10.0
        
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # Should be very small (likely 0.0 with normal distribution)
        assert p_value == 0.0
        
    def test_calculate_pvalue_non_extreme_observed(self):
        """Test p-value calculation with non-extreme observed statistic."""
        null_stats = np.random.normal(0, 1, 1000)
        permutation_results = pd.DataFrame({"statistic": null_stats})
        
        # Observed statistic near mean
        observed_stat = 0.0
        
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # Should be close to 1.0 (all values are >= 0 in absolute terms)
        assert p_value > 0.9
        
    def test_calculate_pvalue_two_tailed(self):
        """Test that p-value calculation is two-tailed."""
        # Create symmetric null distribution
        null_stats = np.array([-2, -1, 0, 1, 2])
        permutation_results = pd.DataFrame({"statistic": null_stats})
        
        # Observed statistic of 1.5
        observed_stat = 1.5
        
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # |1.5| >= |2| is false, |1.5| >= |-2| is false, |1.5| >= |1| is true, etc.
        # So 2 out of 5 values (1 and -1) are less extreme, 3 values (-2, 2, 0) are more or equal?
        # Wait: |1.5| >= |2| -> 1.5 >= 2 -> False
        # |1.5| >= |-2| -> 1.5 >= 2 -> False
        # |1.5| >= |1| -> 1.5 >= 1 -> True
        # |1.5| >= |0| -> 1.5 >= 0 -> True
        # |1.5| >= |-1| -> 1.5 >= 1 -> True
        # So 3 out of 5 = 0.6
        assert p_value == 0.6
        
    def test_calculate_pvalue_empty_null(self):
        """Test that empty null distribution raises error."""
        permutation_results = pd.DataFrame({"statistic": []})
        observed_stat = 1.5
        
        with pytest.raises(ValueError, match="No valid permutation statistics found"):
            calculate_permutation_pvalue(permutation_results, observed_stat)
        
    def test_calculate_pvalue_with_nans(self):
        """Test p-value calculation with NaN values in null distribution."""
        null_stats = np.array([1.0, np.nan, 2.0, np.nan, 3.0])
        permutation_results = pd.DataFrame({"statistic": null_stats})
        
        observed_stat = 2.5
        
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # Should only consider non-NaN values: [1.0, 2.0, 3.0]
        # |2.5| >= |1.0| -> True
        # |2.5| >= |2.0| -> True
        # |2.5| >= |3.0| -> False
        # So 2 out of 3 = 0.666...
        assert abs(p_value - 2/3) < 0.001
        
    def test_calculate_pvalue_identical_values(self):
        """Test p-value when all null stats are identical."""
        null_stats = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        permutation_results = pd.DataFrame({"statistic": null_stats})
        
        observed_stat = 1.0
        
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # All values are equal to observed, so all are >=
        assert p_value == 1.0
        
        observed_stat = 0.5
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # All values are > observed in absolute terms
        assert p_value == 1.0
        
        observed_stat = 2.0
        p_value = calculate_permutation_pvalue(permutation_results, observed_stat)
        
        # No values are >= observed
        assert p_value == 0.0
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])