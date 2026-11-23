"""
Unit tests for the binning logic in bin_feedback_groups.py.

Tests FR-004 boundaries: <2h, 2h–48h, >48h.
"""
import sys
import os
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from bin_feedback_groups import assign_feedback_group, bin_feedback_groups, IMMEDIATE_THRESHOLD, DELAYED_THRESHOLD


class TestAssignFeedbackGroup:
    """Tests for the single-row assignment function."""

    def test_immediate_less_than_2h(self):
        """Test that intervals < 2h are assigned 'Immediate'."""
        test_cases = [0.0, 0.1, 1.9, 1.99]
        for val in test_cases:
            row = {'median_interval_hours': val}
            assert assign_feedback_group(row) == "Immediate"

    def test_immediate_boundary_exclusive(self):
        """Test that exactly 2h is NOT 'Immediate' (should be 'Delayed')."""
        row = {'median_interval_hours': 2.0}
        assert assign_feedback_group(row) == "Delayed"

    def test_delayed_range(self):
        """Test that 2h <= interval <= 48h are assigned 'Delayed'."""
        test_cases = [2.0, 2.1, 24.0, 47.9, 48.0]
        for val in test_cases:
            row = {'median_interval_hours': val}
            assert assign_feedback_group(row) == "Delayed"

    def test_variable_greater_than_48h(self):
        """Test that intervals > 48h are assigned 'Variable'."""
        test_cases = [48.1, 50.0, 100.0, 720.0]
        for val in test_cases:
            row = {'median_interval_hours': val}
            assert assign_feedback_group(row) == "Variable"

    def test_unknown_for_nan(self):
        """Test that NaN intervals are assigned 'Unknown'."""
        row = {'median_interval_hours': np.nan}
        assert assign_feedback_group(row) == "Unknown"


class TestBinningLogic:
    """Tests for the DataFrame-level binning function."""

    def test_dataframe_binning(self):
        """Test that bin_feedback_groups correctly adds the column."""
        data = {
            'learner_id': [1, 2, 3, 4],
            'median_interval_hours': [1.0, 10.0, 48.0, 49.0]
        }
        df = pd.DataFrame(data)
        result = bin_feedback_groups(df)

        assert 'feedback_group' in result.columns
        assert result['feedback_group'].tolist() == ['Immediate', 'Delayed', 'Delayed', 'Variable']

    def test_distribution_counts(self):
        """Verify that the distribution matches expectations for mixed data."""
        data = {
            'learner_id': list(range(10)),
            'median_interval_hours': [0.5, 1.9, 2.0, 10.0, 48.0, 48.1, 100.0, 200.0, 5.0, 50.0]
        }
        df = pd.DataFrame(data)
        result = bin_feedback_groups(df)

        # Expected:
        # Immediate: 0.5, 1.9 (2)
        # Delayed: 2.0, 10.0, 48.0, 5.0 (4)
        # Variable: 48.1, 100.0, 200.0, 50.0 (4)
        counts = result['feedback_group'].value_counts()

        assert counts.get('Immediate', 0) == 2
        assert counts.get('Delayed', 0) == 4
        assert counts.get('Variable', 0) == 4

    def test_constant_thresholds(self):
        """Verify thresholds are set as per FR-004."""
        assert IMMEDIATE_THRESHOLD == 2.0
        assert DELAYED_THRESHOLD == 48.0
