"""
Unit tests for duplicate resolution logic in the preprocessing pipeline.

This module tests the logic implemented in code/ingest/preprocess.py that
resolves duplicate planet entries by keeping the one with the lowest
radius uncertainty.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.ingest.preprocess import resolve_duplicates


class TestResolveDuplicates:
    """Tests for the resolve_duplicates function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a sample DataFrame with duplicates
        self.data = pd.DataFrame({
            'kepler_id': [1, 1, 2, 2, 3],
            'planet_name': ['Kepler-1 b', 'Kepler-1 c', 'Kepler-2 b', 'Kepler-2 c', 'Kepler-3 b'],
            'radius': [1.5, 1.6, 2.0, 2.1, 1.0],
            'radius_uncertainty': [0.10, 0.05, 0.15, 0.20, 0.08],
            'period': [10.0, 10.0, 20.0, 20.0, 30.0],
            'period_uncertainty': [0.01, 0.01, 0.02, 0.02, 0.03],
            'teff': [5500.0, 5500.0, 6000.0, 6000.0, 5000.0],
            'teff_uncertainty': [100.0, 100.0, 150.0, 150.0, 80.0]
        })

    def test_no_duplicates(self):
        """Test that a DataFrame with no duplicates is returned unchanged."""
        no_dup_data = pd.DataFrame({
            'kepler_id': [1, 2, 3],
            'planet_name': ['Kepler-1 b', 'Kepler-2 b', 'Kepler-3 b'],
            'radius': [1.5, 2.0, 1.0],
            'radius_uncertainty': [0.10, 0.15, 0.08],
            'period': [10.0, 20.0, 30.0],
            'period_uncertainty': [0.01, 0.02, 0.03],
            'teff': [5500.0, 6000.0, 5000.0],
            'teff_uncertainty': [100.0, 150.0, 80.0]
        })
        
        result = resolve_duplicates(no_dup_data)
        assert len(result) == len(no_dup_data)
        assert result['kepler_id'].tolist() == no_dup_data['kepler_id'].tolist()

    def test_duplicate_resolution_keeps_lowest_uncertainty(self):
        """Test that duplicates are resolved by keeping the entry with lowest radius uncertainty."""
        result = resolve_duplicates(self.data)
        
        # Should have 3 unique kepler_ids
        assert len(result) == 3
        
        # For kepler_id=1, should keep the one with radius_uncertainty=0.05 (not 0.10)
        kepler_1 = result[result['kepler_id'] == 1]
        assert len(kepler_1) == 1
        assert kepler_1.iloc[0]['radius_uncertainty'] == 0.05
        assert kepler_1.iloc[0]['planet_name'] == 'Kepler-1 c'  # The one with lower uncertainty
        
        # For kepler_id=2, should keep the one with radius_uncertainty=0.15 (not 0.20)
        kepler_2 = result[result['kepler_id'] == 2]
        assert len(kepler_2) == 1
        assert kepler_2.iloc[0]['radius_uncertainty'] == 0.15
        assert kepler_2.iloc[0]['planet_name'] == 'Kepler-2 b'
        
        # kepler_id=3 has no duplicate, should remain unchanged
        kepler_3 = result[result['kepler_id'] == 3]
        assert len(kepler_3) == 1
        assert kepler_3.iloc[0]['radius_uncertainty'] == 0.08

    def test_empty_dataframe(self):
        """Test handling of an empty DataFrame."""
        empty_df = pd.DataFrame(columns=['kepler_id', 'planet_name', 'radius', 'radius_uncertainty'])
        result = resolve_duplicates(empty_df)
        assert len(result) == 0
        assert result.empty

    def test_single_entry(self):
        """Test handling of a DataFrame with a single entry."""
        single_df = pd.DataFrame({
            'kepler_id': [1],
            'planet_name': ['Kepler-1 b'],
            'radius': [1.5],
            'radius_uncertainty': [0.10]
        })
        result = resolve_duplicates(single_df)
        assert len(result) == 1
        assert result.iloc[0]['kepler_id'] == 1

    def test_tie_breaking(self):
        """Test that when uncertainties are equal, the first occurrence is kept."""
        tie_data = pd.DataFrame({
            'kepler_id': [1, 1],
            'planet_name': ['Kepler-1 a', 'Kepler-1 b'],
            'radius': [1.5, 1.6],
            'radius_uncertainty': [0.10, 0.10],  # Equal uncertainties
            'period': [10.0, 10.0],
            'period_uncertainty': [0.01, 0.01],
            'teff': [5500.0, 5500.0],
            'teff_uncertainty': [100.0, 100.0]
        })
        
        result = resolve_duplicates(tie_data)
        assert len(result) == 1
        # Should keep the first occurrence
        assert result.iloc[0]['planet_name'] == 'Kepler-1 a'

    def test_preserves_all_columns(self):
        """Test that all columns are preserved in the output."""
        result = resolve_duplicates(self.data)
        assert list(result.columns) == list(self.data.columns)

    def test_large_dataset_performance(self):
        """Test that the function handles a reasonably large dataset efficiently."""
        # Create a dataset with 1000 entries and 100 duplicates
        large_data = []
        for i in range(100):
            for j in range(10):
                large_data.append({
                    'kepler_id': i,
                    'planet_name': f'Kepler-{i} b{j}',
                    'radius': 1.0 + j * 0.1,
                    'radius_uncertainty': 0.1 + j * 0.01,
                    'period': 10.0 + i,
                    'period_uncertainty': 0.01,
                    'teff': 5500.0,
                    'teff_uncertainty': 100.0
                })
        
        large_df = pd.DataFrame(large_data)
        result = resolve_duplicates(large_df)
        
        # Should have exactly 100 unique entries
        assert len(result) == 100
        # All entries should have the lowest uncertainty (j=0)
        assert all(result['radius_uncertainty'] == 0.1)