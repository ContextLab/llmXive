"""
Unit tests for statistical metrics in utils/metrics.py
"""
import pytest
import numpy as np
from code.utils.metrics import paired_t_test, bonferroni_correct, ks_test


class TestPairedTTest:
    """Tests for the paired_t_test function."""

    def test_identical_sequences(self):
        """When sequences are identical, p-value should be 1.0."""
        seq1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        seq2 = [1.0, 2.0, 3.0, 4.0, 5.0]
        t_stat, p_val = paired_t_test(seq1, seq2)
        assert t_stat == 0.0
        assert p_val == 1.0

    def test_different_sequences(self):
        """Different sequences should produce a non-trivial p-value."""
        # Create sequences with a clear mean difference
        seq1 = [10.0, 11.0, 12.0, 13.0, 14.0]
        seq2 = [20.0, 21.0, 22.0, 23.0, 24.0]
        t_stat, p_val = paired_t_test(seq1, seq2)
        assert t_stat != 0.0
        assert 0.0 <= p_val <= 1.0

    def test_empty_sequence_raises(self):
        """Empty sequences should raise ValueError."""
        with pytest.raises(ValueError):
            paired_t_test([], [1.0, 2.0])

        with pytest.raises(ValueError):
            paired_t_test([1.0, 2.0], [])

    def test_mismatched_lengths_raises(self):
        """Sequences of different lengths should raise ValueError."""
        with pytest.raises(ValueError):
            paired_t_test([1.0, 2.0, 3.0], [1.0, 2.0])


class TestBonferroniCorrect:
    """Tests for the bonferroni_correct function."""

    def test_single_pvalue(self):
        """Correcting a single p-value."""
        p_val = 0.05
        corrected = bonferroni_correct([p_val], n_comparisons=2)
        # Should return a float for single value
        assert isinstance(corrected, float)
        assert corrected == 0.10

    def test_multiple_pvalues(self):
        """Correcting multiple p-values."""
        p_values = [0.01, 0.05, 0.10]
        corrected = bonferroni_correct(p_values, n_comparisons=3)
        assert isinstance(corrected, list)
        assert corrected == [0.03, 0.15, 0.30]

    def test_capping_at_one(self):
        """Corrected p-values should be capped at 1.0."""
        p_values = [0.6, 0.8]
        corrected = bonferroni_correct(p_values, n_comparisons=2)
        assert corrected == [1.0, 1.0]

    def test_empty_input(self):
        """Empty input should return empty list."""
        result = bonferroni_correct([], n_comparisons=5)
        assert result == []

    def test_zero_comparisons_raises(self):
        """Zero or negative n_comparisons should raise ValueError."""
        with pytest.raises(ValueError):
            bonferroni_correct([0.05], n_comparisons=0)

        with pytest.raises(ValueError):
            bonferroni_correct([0.05], n_comparisons=-1)


class TestKSTest:
    """Tests for the ks_test function."""

    def test_identical_distributions(self):
        """Identical distributions should have high p-value."""
        # Using the same data
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        ks_stat, p_val = ks_test(data, data)
        assert ks_stat == 0.0
        assert p_val == 1.0

    def test_different_distributions(self):
        """Different distributions should have low p-value."""
        # Normal vs shifted normal
        np.random.seed(42)
        data1 = np.random.normal(0, 1, 1000)
        data2 = np.random.normal(5, 1, 1000)
        ks_stat, p_val = ks_test(data1, data2)
        assert ks_stat > 0
        assert p_val < 0.05  # Should be significant

    def test_empty_sequence_raises(self):
        """Empty sequences should raise ValueError."""
        with pytest.raises(ValueError):
            ks_test([], [1.0, 2.0])

        with pytest.raises(ValueError):
            ks_test([1.0, 2.0], [])