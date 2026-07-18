"""
Unit tests for src/data/features.py
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

# Add project root to path if not already
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.features import get_element_properties, compute_compositional_features
from src.utils.logging import get_logger

logger = get_logger(__name__)

class TestGetElementProperties:
    def test_valid_element(self):
        """Test fetching properties for a known element."""
        props = get_element_properties("Cu")
        assert props is not None
        assert props['symbol'] == "Cu"
        assert 'atomic_radius' in props
        assert 'electronegativity' in props
        assert 'valence' in props
        assert props['atomic_radius'] > 0
        assert props['electronegativity'] > 0

    def test_invalid_element(self):
        """Test fetching properties for a non-existent element."""
        props = get_element_properties("Xx") # Invalid symbol
        assert props is None

    @patch('src.data.features.mendeleev_element')
    def test_missing_property(self, mock_el):
        """Test handling when mendeleev returns None for a property."""
        mock_el.return_value = MagicMock()
        mock_el.return_value.atomic_radius = None
        mock_el.return_value.electronegativity = 1.5
        mock_el.return_value.valence = 1
        mock_el.return_value.group_number = 11

        # Should return None because radius is missing
        props = get_element_properties("Cu")
        assert props is None

class TestComputeCompositionalFeatures:
    def test_empty_input(self):
        """Test that empty dataframe is handled gracefully."""
        df = pd.DataFrame(columns=['composition'])
        result = compute_compositional_features(df)
        assert result.empty
        assert 'atomic_radius_variance' in result.columns

    def test_single_element(self):
        """Test calculation for a single element alloy."""
        data = {'composition': ['Cu']}
        df = pd.DataFrame(data)
        result = compute_compositional_features(df)
        
        assert not result.empty
        # For a single element, variance and std should be 0
        assert result.iloc[0]['atomic_radius_variance'] == 0.0
        assert result.iloc[0]['electronegativity_std'] == 0.0
        # VEC should be the valence of Cu
        assert result.iloc[0]['valence_electron_concentration'] > 0

    def test_binary_alloy(self):
        """Test calculation for a binary alloy."""
        data = {'composition': ['Cu0.5Al0.5']}
        df = pd.DataFrame(data)
        result = compute_compositional_features(df)

        assert not result.empty
        # Variance and std should be > 0 for different elements
        assert result.iloc[0]['atomic_radius_variance'] > 0
        assert result.iloc[0]['electronegativity_std'] > 0

    def test_invalid_composition_string(self):
        """Test handling of unparseable composition strings."""
        data = {'composition': ['Invalid!!!']}
        df = pd.DataFrame(data)
        result = compute_compositional_features(df)
        
        # Should not crash, but result should be NaN
        assert pd.isna(result.iloc[0]['atomic_radius_variance'])

    def test_missing_element_properties(self):
        """Test handling when an element in the alloy has no properties."""
        # Mock get_element_properties to fail for 'Xx'
        with patch('src.data.features.get_element_properties') as mock_get:
            def side_effect(sym):
                if sym == 'Xx':
                    return None
                return {'atomic_radius': 100, 'electronegativity': 1.0, 'valence': 1}
            mock_get.side_effect = side_effect

            data = {'composition': ['Cu0.5Xx0.5']}
            df = pd.DataFrame(data)
            result = compute_compositional_features(df)

            # Should result in NaN for the row with missing element
            assert pd.isna(result.iloc[0]['atomic_radius_variance'])

    def test_fraction_normalization(self):
        """Test that fractions are normalized correctly."""
        # Input 0.25 Cu and 0.75 Al
        data = {'composition': ['Cu0.25Al0.75']}
        df = pd.DataFrame(data)
        result = compute_compositional_features(df)
        
        # Just check it runs without error and produces numbers
        assert not pd.isna(result.iloc[0]['valence_electron_concentration'])

class TestFeaturesIntegration:
    def test_full_dataframe_processing(self):
        """Test processing a realistic dataframe."""
        data = {
            'id': [1, 2, 3],
            'composition': ['Cu', 'Al', 'Cu0.5Al0.5'],
            'C11': [160, 100, 130],
            'C12': [60, 40, 50],
            'C44': [70, 28, 50]
        }
        df = pd.DataFrame(data)
        result = compute_compositional_features(df)

        assert len(result) == 3
        assert 'atomic_radius_variance' in result.columns
        assert 'electronegativity_std' in result.columns
        assert 'valence_electron_concentration' in result.columns
        
        # Check specific values
        # Row 0 (Cu): variance=0, std=0
        assert result.iloc[0]['atomic_radius_variance'] == 0.0
        # Row 2 (CuAl): variance > 0
        assert result.iloc[2]['atomic_radius_variance'] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])