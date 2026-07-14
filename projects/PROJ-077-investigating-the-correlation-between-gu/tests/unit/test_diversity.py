"""
Unit tests for diversity.py (Shannon Index calculation).
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from diversity import calculate_shannon_index

class TestShannonIndex:
    """Tests for Shannon Index calculation."""

    def test_shannon_calculation_known_values(self):
        """
        Test Shannon calculation with known values.
        Input: 3-row wide taxa matrix with columns ['SpeciesA', 'SpeciesB', 'SpeciesC']
        Values: [[10, 0, 0], [5, 5, 0], [0, 0, 10]]
        Expected:
          Row 0: 10, 0, 0 -> Only one species present. Shannon = 0.0
          Row 1: 5, 5, 0 -> Two species, equal abundance. Shannon = ln(2) ≈ 0.6931
          Row 2: 0, 0, 10 -> Only one species present. Shannon = 0.0
        """
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'SpeciesA': [10, 5, 0],
            'SpeciesB': [0, 5, 0],
            'SpeciesC': [0, 0, 10]
        }
        df = pd.DataFrame(data)

        result = calculate_shannon_index(df, sample_column='participant_id')

        # Verify column exists
        assert 'shannon_index' in result.columns

        # Verify values
        # P1: 0.0
        assert np.isclose(result.loc[result['participant_id'] == 'P1', 'shannon_index'].values[0], 0.0, atol=1e-4)
        
        # P2: ln(2) ≈ 0.693147
        expected_p2 = np.log(2)
        actual_p2 = result.loc[result['participant_id'] == 'P2', 'shannon_index'].values[0]
        assert np.isclose(actual_p2, expected_p2, atol=1e-4)

        # P3: 0.0
        assert np.isclose(result.loc[result['participant_id'] == 'P3', 'shannon_index'].values[0], 0.0, atol=1e-4)

    def test_shannon_with_zeros(self):
        """Test that zeros in counts are handled correctly (ignored in log)."""
        data = {
            'participant_id': ['P1'],
            'TaxaA': [0],
            'TaxaB': [0],
            'TaxaC': [0]
        }
        df = pd.DataFrame(data)
        
        # Should not raise an error, but Shannon of all zeros is undefined (-inf or nan)
        # scikit-bio typically returns 0.0 or nan for all-zero samples depending on version.
        # We expect it to run without crashing.
        result = calculate_shannon_index(df, sample_column='participant_id')
        assert 'shannon_index' in result.columns

    def test_shannon_large_counts(self):
        """Test with large counts to ensure numerical stability."""
        data = {
            'participant_id': ['P1'],
            'TaxaA': [1000],
            'TaxaB': [1000],
            'TaxaC': [1000]
        }
        df = pd.DataFrame(data)
        
        result = calculate_shannon_index(df, sample_column='participant_id')
        # Equal distribution of 3 taxa: ln(3)
        expected = np.log(3)
        assert np.isclose(result['shannon_index'].values[0], expected, atol=1e-4)

    def test_empty_dataframe(self):
        """Test behavior with an empty dataframe."""
        df = pd.DataFrame(columns=['participant_id', 'TaxaA', 'TaxaB'])
        result = calculate_shannon_index(df, sample_column='participant_id')
        assert 'shannon_index' in result.columns
        assert len(result) == 0

    def test_missing_species_column(self):
        """Test that non-numeric columns are handled or ignored."""
        data = {
            'participant_id': ['P1'],
            'TaxaA': [10],
            'TaxaB': ['string_value'] # Non-numeric
        }
        df = pd.DataFrame(data)
        
        # The function should coerce to numeric (filling NaN with 0)
        # and not crash.
        result = calculate_shannon_index(df, sample_column='participant_id')
        assert 'shannon_index' in result.columns