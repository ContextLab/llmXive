"""
Unit tests for Task T019: Bonferroni Correction
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Import the function to test
# Assuming the module is code/task_t019_bonferroni_correction.py
# We need to make sure the import path is correct for the test runner
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from task_t019_bonferroni_correction import apply_bonferroni_correction, OUTCOME_COLUMNS, ALPHA


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction logic."""

    def test_bonferroni_correction_simple(self):
        """Test basic Bonferroni correction calculation."""
        # Simulate raw results for two outcomes
        raw_results = {
            'perseverative_errors': {
                'statistic': 2.5,
                'p_value': 0.01,
                'n_nostalgia': 50,
                'n_control': 50
            },
            'categories_completed': {
                'statistic': 1.8,
                'p_value': 0.04,
                'n_nostalgia': 50,
                'n_control': 50
            }
        }

        corrected = apply_bonferroni_correction(raw_results)

        # Check that we have results for both outcomes
        assert 'perseverative_errors' in corrected
        assert 'categories_completed' in corrected

        # Check corrected p-values (0.01 * 2 = 0.02, 0.04 * 2 = 0.08)
        assert abs(corrected['perseverative_errors']['corrected_p_value'] - 0.02) < 1e-9
        assert abs(corrected['categories_completed']['corrected_p_value'] - 0.08) < 1e-9

        # Check significance (alpha = 0.05, adjusted = 0.025)
        # 0.02 < 0.025 -> True
        # 0.08 > 0.025 -> False
        assert corrected['perseverative_errors']['significant_after_correction'] is True
        assert corrected['categories_completed']['significant_after_correction'] is False

    def test_bonferroni_correction_capped_at_1(self):
        """Test that corrected p-values are capped at 1.0."""
        raw_results = {
            'perseverative_errors': {
                'statistic': 0.5,
                'p_value': 0.6,
                'n_nostalgia': 50,
                'n_control': 50
            }
        }

        corrected = apply_bonferroni_correction(raw_results)

        # 0.6 * 2 = 1.2 -> should be capped at 1.0
        assert corrected['perseverative_errors']['corrected_p_value'] == 1.0
        assert corrected['perseverative_errors']['significant_after_correction'] is False

    def test_bonferroni_correction_missing_pvalue(self):
        """Test handling of missing p-values."""
        raw_results = {
            'perseverative_errors': {
                'statistic': None,
                'p_value': None,
                'n_nostalgia': 50,
                'n_control': 50
            }
        }

        corrected = apply_bonferroni_correction(raw_results)

        assert corrected['perseverative_errors']['corrected_p_value'] is None
        assert corrected['perseverative_errors']['significant_after_correction'] is False

    def test_bonferroni_correction_adjusted_alpha(self):
        """Test that the adjusted alpha is correctly calculated."""
        raw_results = {
            'outcome_1': {'statistic': 1.0, 'p_value': 0.01, 'n_nostalgia': 10, 'n_control': 10},
            'outcome_2': {'statistic': 1.0, 'p_value': 0.01, 'n_nostalgia': 10, 'n_control': 10}
        }

        corrected = apply_bonferroni_correction(raw_results)

        # Check that adjusted_alpha is present and correct (0.05 / 2 = 0.025)
        # Note: The function returns the adjusted_alpha in the result dict
        # We need to check if it's stored. Looking at the implementation, it is stored in the result.
        # But the function doesn't return the global adjusted_alpha, it's per result.
        # Let's check one of the results
        assert abs(corrected['outcome_1']['adjusted_alpha'] - 0.025) < 1e-9
        assert corrected['outcome_1']['correction_method'] == 'bonferroni'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])