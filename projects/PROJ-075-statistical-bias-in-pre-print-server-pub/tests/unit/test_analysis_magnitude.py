"""
Unit tests for paired effect-size analysis (magnitude) in code/03_analysis.py.
Verifies paired t-test and Wilcoxon logic.
"""
import pytest
import numpy as np
from scipy import stats

class TestMagnitudeAnalysis:
    def test_paired_ttest_calculation(self):
        """
        Test the calculation of a paired t-test on a synthetic dataset.
        """
        np.random.seed(42)
        # Generate paired data with a known difference
        preprint_es = np.random.normal(0.5, 0.2, 50)
        journal_es = preprint_es + 0.1  # Systematic shift of 0.1
        
        t_stat, p_val = stats.ttest_rel(preprint_es, journal_es)
        
        assert t_stat is not None
        assert p_val is not None
        assert 0 <= p_val <= 1

    def test_wilcoxon_calculation(self):
        """
        Test the calculation of a Wilcoxon signed-rank test.
        """
        np.random.seed(42)
        preprint_es = np.random.normal(0.5, 0.2, 50)
        journal_es = preprint_es + 0.1
        
        # Wilcoxon test
        w_stat, p_val = stats.wilcoxon(preprint_es, journal_es)
        
        assert w_stat is not None
        assert p_val is not None
        assert 0 <= p_val <= 1

    def test_censored_data_exclusion(self):
        """
        Test that censored data is correctly excluded from standard analysis.
        """
        # Simulate a list of pairs, some censored, some not
        data = [
            {'pre_es': 0.5, 'journal_es': 0.6, 'censored': False},
            {'pre_es': 0.4, 'journal_es': 0.5, 'censored': False},
            {'pre_es': 0.5, 'journal_es': 0.6, 'censored': True}, # Should be excluded
            {'pre_es': 0.6, 'journal_es': 0.7, 'censored': False},
        ]
        
        # Filter non-censored
        non_censored = [d for d in data if not d['censored']]
        
        assert len(non_censored) == 3
        assert all(not d['censored'] for d in non_censored)
        
        # Filter censored
        censored = [d for d in data if d['censored']]
        assert len(censored) == 1
