"""
Unit tests for statistical analysis logic.
"""
import pytest
import sys
import numpy as np
from pathlib import Path

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.stats_analysis import perform_wilcoxon_test, calculate_rank_biserial_correlation


class TestStatsAnalysis:
    """Tests for statistical functions."""

    def test_wilcoxon_test_basic(self):
        """Verify Wilcoxon test runs on sample data."""
        sample_a = np.array([1, 2, 3, 4, 5])
        sample_b = np.array([1.5, 2.5, 3.5, 4.5, 5.5])

        # Should return a statistic and p-value
        stat, pval = perform_wilcoxon_test(sample_a, sample_b)
        assert isinstance(stat, (int, float))
        assert isinstance(pval, (int, float))
        assert 0.0 <= pval <= 1.0

    def test_rank_biserial_correlation(self):
        """Verify rank-biserial correlation calculation."""
        sample_a = np.array([1, 2, 3, 4, 5])
        sample_b = np.array([1.5, 2.5, 3.5, 4.5, 5.5])

        rbc = calculate_rank_biserial_correlation(sample_a, sample_b)
        assert isinstance(rbc, (int, float))
        assert -1.0 <= rbc <= 1.0
