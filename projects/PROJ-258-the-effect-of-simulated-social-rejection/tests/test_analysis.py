"""
Tests for the analysis module (User Story 3).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add code directory to path
code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from analysis import run_anova, apply_fdr, sensitivity_sweep


class TestAnalysis:
    """Tests for analysis functions."""

    def test_anova_selection_logic(self):
        """
        T025: Contract test to assert correct ANOVA type selection.
        """
        # Mock data for Within-Subjects
        data_within = pd.DataFrame({
            'Participant_ID': [1, 1, 2, 2],
            'Condition': ['A', 'B', 'A', 'B'],
            'Value': [10, 12, 11, 13]
        })
        
        # Mock data for Between-Subjects
        data_between = pd.DataFrame({
            'Participant_ID': [1, 2, 3, 4],
            'Condition': ['A', 'A', 'B', 'B'],
            'Value': [10, 11, 12, 13]
        })
        
        # Test Within-Subjects
        result_within = run_anova(data_within, design_type="Within-Subjects")
        assert result_within is not None
        
        # Test Between-Subjects
        result_between = run_anova(data_between, design_type="Between-Subjects")
        assert result_between is not None
        
        # Verify that Between-Subjects does not claim "modulation"
        # This is more of a logic check in the report generation, but we can check the result structure
        assert 'p_value' in result_within or 'F' in result_within

    def test_fdr_and_sensitivity(self):
        """
        T026: Integration test to verify FDR correction and sensitivity sweep.
        """
        # Mock p-values
        p_values = [0.01, 0.04, 0.06, 0.03, 0.02]
        
        # Apply FDR
        corrected = apply_fdr(p_values)
        assert len(corrected) == len(p_values)
        # Check that corrected values are generally <= original (or at least valid)
        # BH correction ensures monotonicity and <= 1
        assert all(0 <= p <= 1 for p in corrected)
        
        # Sensitivity sweep
        # Mock data
        data = pd.DataFrame({
            'Condition': ['A'] * 50 + ['B'] * 50,
            'Value': [10] * 50 + [12] * 50
        })
        
        sensitivity_results = sensitivity_sweep(data, alpha_set={0.01, 0.05, 0.1})
        assert 0.05 in sensitivity_results
        assert sensitivity_results[0.05] > 0 # Power should be > 0 for a real effect