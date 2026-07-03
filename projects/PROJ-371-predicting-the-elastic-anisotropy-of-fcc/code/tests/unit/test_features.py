"""
Unit tests for feature engineering module (T014).
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.features import compute_compositional_features, get_element_properties
from src.utils.config import get_path


class TestGetElementProperties:
    """Tests for get_element_properties function"""

    def test_valid_element(self):
        """Test fetching properties for a valid element"""
        props = get_element_properties('Cu')
        assert props is not None
        assert 'radius' in props
        assert 'electronegativity' in props
        assert 'valence_electrons' in props
        assert props['radius'] > 0
        assert props['electronegativity'] > 0
        assert props['valence_electrons'] > 0

    def test_invalid_element(self):
        """Test handling of invalid element symbol"""
        props = get_element_properties('Xx')
        assert props is None

    def test_different_elements(self):
        """Test fetching properties for different elements"""
        cu_props = get_element_properties('Cu')
        al_props = get_element_properties('Al')
        
        assert cu_props is not None
        assert al_props is not None
        
        # Different elements should have different properties
        assert cu_props['radius'] != al_props['radius']
        assert cu_props['electronegativity'] != al_props['electronegativity']


class TestComputeCompositionalFeatures:
    """Tests for compute_compositional_features function"""

    @pytest.fixture
    def single_element_df(self):
        """Create a dataframe with single element compositions"""
        data = {
            'element': ['Cu', 'Al', 'Ni', 'Ag'],
            'C11': [168, 108, 246, 124],
            'C12': [121, 61, 147, 93],
            'C44': [75, 28, 124, 46],
            'A1': [1.59, 1.14, 1.68, 1.55]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def multi_element_df(self):
        """Create a dataframe with multi-element compositions"""
        data = {
            'element': ['Cu,Al', 'Ni,Cu', 'Ag,Au'],
            'C11': [168, 246, 124],
            'C12': [121, 147, 93],
            'C44': [75, 124, 46],
            'A1': [1.59, 1.68, 1.55]
        }
        return pd.DataFrame(data)

    def test_single_element_variance_zero(self, single_element_df):
        """Test that single element compositions have zero variance"""
        result = compute_compositional_features(single_element_df, 'element')
        
        assert 'atomic_radius_variance' in result.columns
        assert 'electronegativity_std' in result.columns
        assert 'vec' in result.columns
        
        # For single elements, variance and std should be 0
        assert all(result['atomic_radius_variance'] == 0)
        assert all(result['electronegativity_std'] == 0)
        
        # VEC should be positive
        assert all(result['vec'] > 0)

    def test_multi_element_variance_positive(self, multi_element_df):
        """Test that multi-element compositions have positive variance"""
        result = compute_compositional_features(multi_element_df, 'element')
        
        assert 'atomic_radius_variance' in result.columns
        assert 'electronegativity_std' in result.columns
        assert 'vec' in result.columns
        
        # For multi-element, variance and std should be > 0
        assert all(result['atomic_radius_variance'] > 0)
        assert all(result['electronegativity_std'] > 0)

    def test_missing_column_raises(self):
        """Test that missing composition column raises error"""
        df = pd.DataFrame({'C11': [100]})
        with pytest.raises(ValueError):
            compute_compositional_features(df, 'nonexistent_col')

    def test_handles_missing_properties(self):
        """Test handling of elements with missing properties"""
        data = {
            'element': ['Cu', 'Xx', 'Al'],  # Xx is invalid
            'C11': [168, 100, 108],
            'C12': [121, 50, 61],
            'C44': [75, 30, 28]
        }
        df = pd.DataFrame(data)
        
        # Should skip invalid elements and return only valid ones
        result = compute_compositional_features(df, 'element')
        
        # Should have 2 valid rows (Cu and Al)
        assert len(result) == 2
        assert 'atomic_radius_variance' in result.columns

    def test_output_columns_added(self, single_element_df):
        """Test that all expected feature columns are added"""
        result = compute_compositional_features(single_element_df, 'element')
        
        expected_cols = ['atomic_radius_variance', 'electronegativity_std', 'vec']
        for col in expected_cols:
            assert col in result.columns

    def test_preserves_original_data(self, single_element_df):
        """Test that original columns are preserved"""
        result = compute_compositional_features(single_element_df, 'element')
        
        original_cols = ['element', 'C11', 'C12', 'C44', 'A1']
        for col in original_cols:
            assert col in result.columns
            # Values should be preserved
            pd.testing.assert_series_equal(result[col], single_element_df[col])


class TestFeaturesIntegration:
    """Integration tests for feature engineering"""

    def test_computes_realistic_values(self):
        """Test that computed values are within realistic ranges"""
        data = {
            'element': ['Cu', 'Al', 'Ni'],
            'C11': [168, 108, 246],
            'C12': [121, 61, 147],
            'C44': [75, 28, 124],
            'A1': [1.59, 1.14, 1.68]
        }
        df = pd.DataFrame(data)
        
        result = compute_compositional_features(df, 'element')
        
        # VEC for common FCC metals: Cu=11, Al=3, Ni=10 (approximate)
        # Values should be positive and reasonable
        assert all(result['vec'] > 0)
        assert all(result['vec'] < 20)  # Reasonable upper bound
        
        # Electronegativity std should be 0 for single elements
        assert all(result['electronegativity_std'] == 0)

    def test_empty_input_handling(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame(columns=['element', 'C11', 'C12', 'C44', 'A1'])
        
        with pytest.raises(ValueError):
            compute_compositional_features(df, 'element')