"""
Unit tests for the HEA sample filtering logic in src/data/filter.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.filter import count_principal_elements, filter_hea_samples


class TestCountPrincipalElements:
    """Tests for the count_principal_elements function."""

    def test_count_five_elements_above_threshold(self):
        """Test counting 5 elements above threshold."""
        data = {
            'composition_Fe': 0.2,
            'composition_Co': 0.2,
            'composition_Ni': 0.2,
            'composition_Cr': 0.2,
            'composition_Mn': 0.2,
            'composition_Al': 0.0
        }
        row = pd.Series(data)
        composition_cols = [col for col in data.keys() if col.startswith('composition_')]
        
        count = count_principal_elements(row, composition_cols, threshold=0.01)
        
        assert count == 5

    def test_count_three_elements_above_threshold(self):
        """Test counting 3 elements above threshold."""
        data = {
            'composition_Fe': 0.33,
            'composition_Co': 0.33,
            'composition_Ni': 0.33,
            'composition_Cr': 0.01,
            'composition_Mn': 0.0
        }
        row = pd.Series(data)
        composition_cols = [col for col in data.keys() if col.startswith('composition_')]
        
        count = count_principal_elements(row, composition_cols, threshold=0.01)
        
        assert count == 3

    def test_count_zero_elements_above_threshold(self):
        """Test counting 0 elements above threshold."""
        data = {
            'composition_Fe': 0.005,
            'composition_Co': 0.005,
            'composition_Ni': 0.005
        }
        row = pd.Series(data)
        composition_cols = [col for col in data.keys() if col.startswith('composition_')]
        
        count = count_principal_elements(row, composition_cols, threshold=0.01)
        
        assert count == 0

    def test_count_with_empty_columns(self):
        """Test counting with empty composition columns list."""
        row = pd.Series({'composition_Fe': 0.5})
        
        count = count_principal_elements(row, [], threshold=0.01)
        
        assert count == 0

    def test_count_with_higher_threshold(self):
        """Test counting with a higher threshold."""
        data = {
            'composition_Fe': 0.25,
            'composition_Co': 0.25,
            'composition_Ni': 0.25,
            'composition_Cr': 0.20,
            'composition_Mn': 0.05
        }
        row = pd.Series(data)
        composition_cols = [col for col in data.keys() if col.startswith('composition_')]
        
        # With threshold 0.1, only 4 should count
        count = count_principal_elements(row, composition_cols, threshold=0.1)
        
        assert count == 4


class TestFilterHEASamples:
    """Tests for the filter_hea_samples function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.composition_cols = [
            'composition_Fe', 'composition_Co', 'composition_Ni',
            'composition_Cr', 'composition_Mn', 'composition_Al'
        ]
        
        # Create a sample DataFrame
        self.df = pd.DataFrame([
            # 5 elements, valid BM
            {**{col: 0.2 for col in self.composition_cols[:5]}, 'composition_Al': 0.0, 'bulk_modulus': 150.0, 'id': 1},
            # 4 elements, valid BM (should be filtered)
            {**{col: 0.25 for col in self.composition_cols[:4]}, 'composition_Mn': 0.0, 'composition_Al': 0.0, 'bulk_modulus': 160.0, 'id': 2},
            # 6 elements, valid BM
            {**{col: 0.166 for col in self.composition_cols}, 'bulk_modulus': 170.0, 'id': 3},
            # 5 elements, NaN BM (should be filtered)
            {**{col: 0.2 for col in self.composition_cols[:5]}, 'composition_Al': 0.0, 'bulk_modulus': np.nan, 'id': 4},
            # 5 elements, zero BM (should be filtered)
            {**{col: 0.2 for col in self.composition_cols[:5]}, 'composition_Al': 0.0, 'bulk_modulus': 0.0, 'id': 5},
            # 5 elements, negative BM (should be filtered)
            {**{col: 0.2 for col in self.composition_cols[:5]}, 'composition_Al': 0.0, 'bulk_modulus': -10.0, 'id': 6},
            # 5 elements, valid BM
            {**{col: 0.2 for col in self.composition_cols[:5]}, 'composition_Al': 0.0, 'bulk_modulus': 180.0, 'id': 7},
        ])

    def test_filter_retains_samples_with_5_elements_and_valid_bm(self):
        """Test that samples with ≥5 elements and valid BM are retained."""
        filtered_df, stats = filter_hea_samples(
            self.df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=5
        )
        
        # Should retain ids 1, 3, 7
        assert len(filtered_df) == 3
        assert set(filtered_df['id'].tolist()) == {1, 3, 7}
        
        assert stats['initial_count'] == 7
        assert stats['final_count'] == 3
        assert stats['removed_by_element_count'] == 1  # id 2
        assert stats['removed_by_bulk_modulus'] == 3    # ids 4, 5, 6

    def test_filter_removes_samples_with_less_than_5_elements(self):
        """Test that samples with <5 elements are removed."""
        filtered_df, stats = filter_hea_samples(
            self.df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=5
        )
        
        # id 2 has only 4 elements, should be removed
        assert 2 not in filtered_df['id'].tolist()

    def test_filter_removes_samples_with_nan_bulk_modulus(self):
        """Test that samples with NaN Bulk Modulus are removed."""
        filtered_df, stats = filter_hea_samples(
            self.df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=5
        )
        
        # id 4 has NaN BM, should be removed
        assert 4 not in filtered_df['id'].tolist()

    def test_filter_removes_samples_with_zero_or_negative_bulk_modulus(self):
        """Test that samples with zero or negative Bulk Modulus are removed."""
        filtered_df, stats = filter_hea_samples(
            self.df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=5
        )
        
        # ids 5 and 6 have invalid BM, should be removed
        assert 5 not in filtered_df['id'].tolist()
        assert 6 not in filtered_df['id'].tolist()

    def test_filter_empty_dataframe(self):
        """Test filtering an empty DataFrame."""
        empty_df = pd.DataFrame(columns=self.composition_cols + ['bulk_modulus'])
        
        filtered_df, stats = filter_hea_samples(
            empty_df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=5
        )
        
        assert len(filtered_df) == 0
        assert stats['initial_count'] == 0
        assert stats['final_count'] == 0

    def test_filter_all_samples_removed(self):
        """Test when all samples are filtered out."""
        df_all_invalid = pd.DataFrame([
            {'composition_Fe': 0.5, 'composition_Co': 0.5, 'bulk_modulus': 150.0},
            {'composition_Fe': 0.5, 'composition_Co': 0.5, 'bulk_modulus': np.nan},
        ])
        
        filtered_df, stats = filter_hea_samples(
            df_all_invalid,
            composition_columns=['composition_Fe', 'composition_Co'],
            bulk_modulus_column='bulk_modulus',
            min_elements=5
        )
        
        assert len(filtered_df) == 0
        assert stats['final_count'] == 0
        assert stats['removed_by_element_count'] == 2

    def test_custom_min_elements(self):
        """Test with custom min_elements parameter."""
        # With min_elements=4, id 2 should be retained
        filtered_df, stats = filter_hea_samples(
            self.df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=4
        )
        
        # Should retain ids 1, 2, 3, 7 (id 2 has 4 elements now)
        assert len(filtered_df) == 4
        assert 2 in filtered_df['id'].tolist()

    def test_custom_min_bulk_modulus(self):
        """Test with custom min_bulk_modulus parameter."""
        # With min_bulk_modulus=165, ids 1 and 2 (if retained) should be removed
        filtered_df, stats = filter_hea_samples(
            self.df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=5,
            min_bulk_modulus=165.0
        )
        
        # Should retain only ids 3 (170) and 7 (180)
        assert len(filtered_df) == 2
        assert set(filtered_df['id'].tolist()) == {3, 7}

    def test_statistics_accuracy(self):
        """Test that statistics are calculated correctly."""
        filtered_df, stats = filter_hea_samples(
            self.df,
            composition_columns=self.composition_cols,
            bulk_modulus_column='bulk_modulus',
            min_elements=5
        )
        
        assert stats['initial_count'] == 7
        assert stats['final_count'] == 3
        assert stats['removed_by_element_count'] == 1
        assert stats['removed_by_bulk_modulus'] == 3
        assert stats['removed_by_nan_bulk_modulus'] == 1
        assert stats['removed_by_low_bulk_modulus'] == 2
        assert stats['min_elements_applied'] == 5
        assert stats['min_bulk_modulus_applied'] == 0.0
        assert stats['min_threshold_applied'] == 0.01