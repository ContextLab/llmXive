"""
Contract tests to verify simulation engine API compliance.
"""
import pytest
from simulation_engine import (
    clopper_pearson_interval,
    execute_t_test,
    execute_anova,
    execute_chi_squared,
    execute_fisher_exact,
    run_single_test_replicate
)

class TestClopperPearsonInterval:
    def test_interval_bounds(self):
        """Test that CI bounds are within [0, 1]."""
        low, high = clopper_pearson_interval(5, 100)
        assert 0.0 <= low <= high <= 1.0

    def test_interval_width(self):
        """Test that CI width decreases with more samples."""
        low1, high1 = clopper_pearson_interval(10, 100)
        low2, high2 = clopper_pearson_interval(10, 1000)
        assert (high2 - low2) < (high1 - low1)

class TestExecuteTTest:
    def test_returns_pvalue(self):
        """Test that t-test returns a valid p-value."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [2.0, 3.0, 4.0]
        pval, _ = execute_t_test(group1, group2)
        assert 0.0 <= pval <= 1.0

class TestExecuteANOVA:
    def test_returns_pvalue(self):
        """Test that ANOVA returns a valid p-value."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [2.0, 3.0, 4.0]
        group3 = [3.0, 4.0, 5.0]
        pval, _ = execute_anova(group1, group2, group3)
        assert 0.0 <= pval <= 1.0

class TestExecuteChiSquared:
    def test_returns_pvalue(self):
        """Test that Chi-squared returns a valid p-value."""
        observed = [[10, 20], [30, 40]]
        pval, _ = execute_chi_squared(observed)
        assert 0.0 <= pval <= 1.0

class TestRunSingleTestReplicate:
    def test_returns_classification(self):
        """Test that replicate returns correct classification structure."""
        np.random.seed(42)
        n = 50
        result = run_single_test_replicate(
            n, 't_test', 'normal', 'null', 0.05, 0.0
        )
        assert 'reject' in result
        assert 'p_value' in result
