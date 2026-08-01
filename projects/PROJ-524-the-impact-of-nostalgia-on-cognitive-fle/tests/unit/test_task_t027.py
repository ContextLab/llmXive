"""
Unit tests for code/task_t027_robustness_check.py.
Tests MMSE-based robustness filtering logic.
"""
import pytest
import pandas as pd
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t027_robustness_check import (
    load_mmse_flag,
    filter_by_mmse
)


class TestFilterByMMSE:
    def test_filter_by_mmse_above_threshold(self):
        """Test filtering keeps participants with MMSE >= threshold."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'MMSE': [28, 24, 22],
            'perseverative_errors': [10, 12, 8]
        })

        result = filter_by_mmse(df, threshold=24)

        assert len(result) == 2
        assert all(result['MMSE'] >= 24)

    def test_filter_by_mmse_below_threshold(self):
        """Test filtering excludes participants with MMSE < threshold."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'MMSE': [20, 18, 15],
            'perseverative_errors': [10, 12, 8]
        })

        result = filter_by_mmse(df, threshold=24)

        assert len(result) == 0

    def test_filter_by_mmse_no_mmse_column(self):
        """Test filtering when MMSE column is missing."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'perseverative_errors': [10, 12]
        })

        result = filter_by_mmse(df, threshold=24)

        # Should return empty or original depending on implementation
        # Based on task description, if no MMSE, it should be skipped
        assert len(result) == 0

    def test_filter_by_mmse_mixed_values(self):
        """Test filtering with mixed MMSE values."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'MMSE': [29, 24, 23, 25, 20],
            'perseverative_errors': [10, 12, 8, 15, 11]
        })

        result = filter_by_mmse(df, threshold=24)

        assert len(result) == 3
        assert set(result['participant_id'].tolist()) == {'P1', 'P2', 'P4'}
        assert all(result['MMSE'] >= 24)

    def test_filter_by_mmse_custom_threshold(self):
        """Test filtering with custom threshold."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'MMSE': [26, 24, 22],
            'perseverative_errors': [10, 12, 8]
        })

        result = filter_by_mmse(df, threshold=26)

        assert len(result) == 1
        assert result.iloc[0]['participant_id'] == 'P1'
        assert result.iloc[0]['MMSE'] == 26
