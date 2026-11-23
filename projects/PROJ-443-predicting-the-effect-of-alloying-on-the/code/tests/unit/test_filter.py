"""
Unit tests for the HEA sample filtering logic.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.filter import count_principal_elements, filter_hea_samples, MIN_PRINCIPAL_ELEMENTS, MIN_COMPOSITION_THRESHOLD


class TestCountPrincipalElements:
    """Tests for the count_principal_elements function."""

    def test_count_with_five_principal_elements(self):
        """Test counting 5 elements above threshold."""
        data = {
            'element_Fe': 0.20,
            'element_Cr': 0.20,
            'element_Ni': 0.20,
            'element_Mn': 0.20,
            'element_Al': 0.20,
            'element_Cu': 0.00
        }
        row = pd.Series(data)
        composition_cols = [c for c in data.keys() if c.startswith('element_')]
        
        count = count_principal_elements(row, composition_cols, threshold=0.05)
        assert count == 5

    def test_count_with_four_principal_elements(self):
        """Test counting 4 elements above threshold."""
        data = {
            'element_Fe': 0.25,
            'element_Cr': 0.25,
            'element_Ni': 0.25,
            'element_Mn': 0.25,
            'element_Al': 0.00,
            'element_Cu': 0.00
        }
        row = pd.Series(data)
        composition_cols = [c for c in data.keys() if c.startswith('element_')]
        
        count = count_principal_elements(row, composition_cols, threshold=0.05)
        assert count == 4

    def test_count_with_nan_values(self):
        """Test handling of NaN values in composition."""
        data = {
            'element_Fe': 0.20,
            'element_Cr': np.nan,
            'element_Ni': 0.20,
            'element_Mn': 0.20,
            'element_Al': 0.20,
        }
        row = pd.Series(data)
        composition_cols = [c for c in data.keys() if c.startswith('element_')]
        
        count = count_principal_elements(row, composition_cols, threshold=0.05)
        # NaN should be treated as 0, so 4 elements
        assert count == 4

    def test_count_with_zero_threshold(self):
        """Test with threshold of 0.0 (all non-zero elements count)."""
        data = {
            'element_Fe': 0.20,
            'element_Cr': 0.00,
            'element_Ni': 0.01,
            'element_Mn': 0.00,
            'element_Al': 0.79,
        }
        row = pd.Series(data)
        composition_cols = [c for c in data.keys() if c.startswith('element_')]
        
        count = count_principal_elements(row, composition_cols, threshold=0.0)
        assert count == 3


class TestFilterHEASamples:
    """Tests for the filter_hea_samples function."""

    def setup_method(self):
        """Set up test data."""
        self.composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn', 'element_Al', 'element_Cu']
        
        self.valid_data = pd.DataFrame({
            'element_Fe': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Cr': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Ni': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Mn': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Al': [0.20, 0.00, 0.40, 0.20, 0.20],
            'element_Cu': [0.00, 0.00, 0.00, 0.00, 0.00],
            'Bulk_Modulus': [150.0, 160.0, 140.0, 155.0, 145.0],
            'sample_id': [1, 2, 3, 4, 5]
        })
        
        self.invalid_bulk_modulus_data = pd.DataFrame({
            'element_Fe': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Cr': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Ni': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Mn': [0.20, 0.25, 0.15, 0.20, 0.20],
            'element_Al': [0.20, 0.00, 0.40, 0.20, 0.20],
            'element_Cu': [0.00, 0.00, 0.00, 0.00, 0.00],
            'Bulk_Modulus': [150.0, np.nan, 140.0, -10.0, 145.0],
            'sample_id': [1, 2, 3, 4, 5]
        })
        
        self.low_element_count_data = pd.DataFrame({
            'element_Fe': [0.50, 0.25, 0.15, 0.20, 0.20],
            'element_Cr': [0.50, 0.25, 0.15, 0.20, 0.20],
            'element_Ni': [0.00, 0.25, 0.15, 0.20, 0.20],
            'element_Mn': [0.00, 0.25, 0.15, 0.20, 0.20],
            'element_Al': [0.00, 0.00, 0.40, 0.20, 0.20],
            'element_Cu': [0.00, 0.00, 0.00, 0.00, 0.00],
            'Bulk_Modulus': [150.0, 160.0, 140.0, 155.0, 145.0],
            'sample_id': [1, 2, 3, 4, 5]
        })

    def test_filter_all_valid(self):
        """Test filtering with all valid samples."""
        filtered_df, stats = filter_hea_samples(
            self.valid_data,
            min_elements=5,
            composition_threshold=0.05
        )
        
        assert len(filtered_df) == 5
        assert stats['total_input'] == 5
        assert stats['total_output'] == 5
        assert stats['dropped_by_bulk_modulus'] == 0
        assert stats['dropped_by_elements'] == 0

    def test_filter_invalid_bulk_modulus(self):
        """Test filtering removes samples with invalid Bulk Modulus."""
        filtered_df, stats = filter_hea_samples(
            self.invalid_bulk_modulus_data,
            min_elements=5,
            composition_threshold=0.05
        )
        
        # Should keep samples 1, 3, 5 (indices 0, 2, 4)
        assert len(filtered_df) == 3
        assert stats['total_input'] == 5
        assert stats['total_output'] == 3
        assert stats['dropped_by_bulk_modulus'] == 2
        assert stats['dropped_by_elements'] == 0
        
        # Check specific sample IDs
        assert 2 not in filtered_df['sample_id'].values
        assert 4 not in filtered_df['sample_id'].values

    def test_filter_low_element_count(self):
        """Test filtering removes samples with < 5 principal elements."""
        filtered_df, stats = filter_hea_samples(
            self.low_element_count_data,
            min_elements=5,
            composition_threshold=0.05
        )
        
        # Sample 1 has only 2 elements >= 0.05, Sample 2 has 4
        # Samples 3, 4, 5 have 5 elements >= 0.05
        assert len(filtered_df) == 3
        assert stats['total_input'] == 5
        assert stats['total_output'] == 3
        assert stats['dropped_by_bulk_modulus'] == 0
        assert stats['dropped_by_elements'] == 2
        
        # Check specific sample IDs
        assert 1 not in filtered_df['sample_id'].values
        assert 2 not in filtered_df['sample_id'].values

    def test_filter_empty_dataframe(self):
        """Test filtering an empty DataFrame."""
        empty_df = pd.DataFrame(columns=self.composition_cols + ['Bulk_Modulus', 'sample_id'])
        filtered_df, stats = filter_hea_samples(
            empty_df,
            min_elements=5,
            composition_threshold=0.05
        )
        
        assert len(filtered_df) == 0
        assert stats['total_input'] == 0
        assert stats['total_output'] == 0

    def test_filter_with_custom_threshold(self):
        """Test filtering with a custom composition threshold."""
        # With threshold 0.1, sample 3 (0.15, 0.15, 0.15, 0.15, 0.40) has 5 elements
        # Sample 4 (0.20, 0.20, 0.20, 0.20, 0.20) has 5 elements
        # Sample 5 (0.20, 0.20, 0.20, 0.20, 0.20) has 5 elements
        # Sample 1 (0.50, 0.50, 0.00, 0.00, 0.00) has 2 elements
        # Sample 2 (0.25, 0.25, 0.25, 0.25, 0.00) has 4 elements
        
        filtered_df, stats = filter_hea_samples(
            self.low_element_count_data,
            min_elements=5,
            composition_threshold=0.1
        )
        
        assert len(filtered_df) == 3
        assert stats['dropped_by_elements'] == 2

    def test_filter_missing_bulk_modulus_column(self):
        """Test filtering when Bulk Modulus column is missing."""
        df_no_bm = self.valid_data.drop(columns=['Bulk_Modulus'])
        filtered_df, stats = filter_hea_samples(
            df_no_bm,
            min_elements=5,
            composition_threshold=0.05
        )
        
        # Should keep all samples since BM filter is skipped
        assert len(filtered_df) == 5
        assert stats['dropped_by_bulk_modulus'] == 0