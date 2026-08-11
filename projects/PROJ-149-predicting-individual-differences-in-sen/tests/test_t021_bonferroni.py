import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code_09_apply_bonferroni import apply_bonferroni_correction, load_correlations

class TestBonferroniCorrection:
    """Tests for T021 Bonferroni correction logic."""

    def test_bonferroni_calculation(self):
        """Verify p-value multiplication and threshold logic."""
        # Create a mock dataframe
        data = {
            'band': ['delta', 'theta', 'alpha', 'beta', 'gamma', 'high_beta'],
            'p_value': [0.001, 0.005, 0.009, 0.01, 0.008, 0.0001],
            'r': [0.3, 0.4, 0.2, 0.1, 0.35, 0.5]
        }
        df = pd.DataFrame(data)

        result = apply_bonferroni_correction(df)

        # Expected threshold: 0.05 / 6 = 0.008333...
        expected_threshold = 0.05 / 6
        assert abs(result['threshold'].iloc[0] - expected_threshold) < 1e-6

        # Check p_corrected calculation (p * 6)
        expected_p_corrected = df['p_value'] * 6
        pd.testing.assert_series_equal(result['p_corrected'], expected_p_corrected)

        # Check significant flags
        # delta: 0.001 < 0.00833 -> True
        # theta: 0.005 < 0.00833 -> True
        # alpha: 0.009 > 0.00833 -> False
        # beta: 0.01 > 0.00833 -> False
        # gamma: 0.008 < 0.00833 -> True
        # high_beta: 0.0001 < 0.00833 -> True
        expected_significant = [True, True, False, False, True, True]
        assert result['significant'].tolist() == expected_significant

    def test_p_corrected_capped_at_1(self):
        """Verify that p_corrected does not exceed 1.0."""
        data = {
            'band': ['delta'],
            'p_value': [0.2],
            'r': [0.1]
        }
        df = pd.DataFrame(data)
        result = apply_bonferroni_correction(df)
        
        assert result['p_corrected'].iloc[0] == 1.0
        assert result['significant'].iloc[0] == False

    def test_empty_dataframe(self):
        """Verify behavior on empty input."""
        df = pd.DataFrame(columns=['band', 'p_value', 'r'])
        result = apply_bonferroni_correction(df)
        assert result.empty
        assert 'p_corrected' in result.columns
        assert 'significant' in result.columns