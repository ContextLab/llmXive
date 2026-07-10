"""
Unit tests for the binning logic (T019).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.binning import assign_bins, LOW_VOLTAGE_THRESHOLD, HIGH_VOLTAGE_TARGET

class TestAssignBins:
    """Tests for the assign_bins function."""

    def test_low_voltage_assignment(self):
        """Test that potentials <= 2V are assigned 'Low'."""
        data = pd.DataFrame({
            'molecule_id': ['M1', 'M2', 'M3'],
            'potential_v': [0.0, 2.0, 1.5]
        })
        result = assign_bins(data)
        assert all(result['bin'] == 'Low')

    def test_high_voltage_assignment(self):
        """Test that potentials == 4V are assigned 'High'."""
        data = pd.DataFrame({
            'molecule_id': ['M4', 'M5'],
            'potential_v': [4.0, 4.0000001] # Test float tolerance
        })
        result = assign_bins(data)
        assert all(result['bin'] == 'High')

    def test_unknown_voltage_assignment(self):
        """Test that potentials outside defined ranges are assigned 'Unknown'."""
        data = pd.DataFrame({
            'molecule_id': ['M6', 'M7'],
            'potential_v': [3.0, 5.0]
        })
        result = assign_bins(data)
        assert all(result['bin'] == 'Unknown')

    def test_missing_potential(self):
        """Test handling of missing potential values."""
        data = pd.DataFrame({
            'molecule_id': ['M8'],
            'potential_v': [np.nan]
        })
        result = assign_bins(data)
        assert result.iloc[0]['bin'] == 'Unknown'

    def test_mixed_data(self):
        """Test a mix of low, high, and unknown potentials."""
        data = pd.DataFrame({
            'molecule_id': ['Mix1', 'Mix2', 'Mix3', 'Mix4'],
            'potential_v': [0.0, 2.0, 4.0, 3.0]
        })
        result = assign_bins(data)
        expected_bins = ['Low', 'Low', 'High', 'Unknown']
        assert list(result['bin']) == expected_bins

    def test_deviation_note_mapping(self):
        """
        Verify the deviation note logic: 4V is the only 'High' bin.
        The spec mentions 3-5V, but we only have 4V data points available.
        This test ensures 3V and 5V are NOT mapped to High (to prevent accidental
        assumption that the range is covered).
        """
        data = pd.DataFrame({
            'molecule_id': ['Dev1', 'Dev2', 'Dev3'],
            'potential_v': [3.0, 5.0, 4.0]
        })
        result = assign_bins(data)
        assert result.loc[result['molecule_id'] == 'Dev1', 'bin'].values[0] == 'Unknown'
        assert result.loc[result['molecule_id'] == 'Dev2', 'bin'].values[0] == 'Unknown'
        assert result.loc[result['molecule_id'] == 'Dev3', 'bin'].values[0] == 'High'