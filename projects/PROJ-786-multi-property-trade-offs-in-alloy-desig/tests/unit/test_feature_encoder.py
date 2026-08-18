"""
Unit tests for feature_encoder.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.feature_encoder import encode_composition, encode_dataframe, get_periodic_property

class TestGetPeriodicProperty:
    def test_atomic_radius_iron(self):
        val = get_periodic_property('Fe', 'atomic_radius')
        assert val is not None
        assert val > 0
        assert isinstance(val, float)

    def test_electronegativity_copper(self):
        val = get_periodic_property('Cu', 'electronegativity')
        assert val is not None
        assert val > 0

    def test_invalid_element(self):
        val = get_periodic_property('XX', 'atomic_radius')
        assert val is None

class TestEncodeComposition:
    def test_simple_binary(self):
        frac, desc = encode_composition("Fe0.5Ni0.5")
        assert 'Fe' in frac
        assert 'Ni' in frac
        assert abs(frac['Fe'] - 0.5) < 1e-6
        assert abs(frac['Ni'] - 0.5) < 1e-6
        assert 'atomic_radius' in desc['Fe']
        assert 'electronegativity' in desc['Fe']

    def test_implicit_stoichiometry(self):
        frac, desc = encode_composition("FeNi")
        assert 'Fe' in frac
        assert 'Ni' in frac
        assert abs(frac['Fe'] - 0.5) < 1e-6
        assert abs(frac['Ni'] - 0.5) < 1e-6

    def test_complex_composition(self):
        frac, desc = encode_composition("Fe0.8Ni0.1Cr0.1")
        assert abs(frac['Fe'] - 0.8) < 1e-6
        assert abs(frac['Ni'] - 0.1) < 1e-6
        assert abs(frac['Cr'] - 0.1) < 1e-6

    def test_invalid_composition(self):
        with pytest.raises(ValueError):
            encode_composition("InvalidString")

class TestEncodeDataFrame:
    def test_encode_simple_df(self):
        data = {
            'composition': ['Fe0.5Ni0.5', 'Fe0.8Ni0.2', 'Cu0.5Zn0.5'],
            'bulk_modulus': [100.0, 110.0, 130.0],
            'shear_modulus': [50.0, 55.0, 65.0]
        }
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df)
        
        # Check columns
        assert 'frac_Fe' in encoded.columns
        assert 'frac_Ni' in encoded.columns
        assert 'frac_Cu' in encoded.columns
        assert 'frac_Zn' in encoded.columns
        assert 'avg_atomic_radius' in encoded.columns
        assert 'var_atomic_radius' in encoded.columns
        
        # Check values
        assert encoded['frac_Fe'].iloc[0] == 0.5
        assert encoded['frac_Ni'].iloc[0] == 0.5
        assert encoded['frac_Cu'].iloc[2] == 0.5
        
        # Check no NaN in key features
        feature_cols = [c for c in encoded.columns if c.startswith('frac_') or c.startswith('avg_')]
        assert encoded[feature_cols].isnull().sum().sum() == 0

    def test_encode_with_missing_data(self):
        data = {
            'composition': ['Fe0.5Ni0.5', 'Invalid', 'Cu0.5Zn0.5'],
            'bulk_modulus': [100.0, 110.0, 130.0]
        }
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df)
        
        # Should drop the invalid row
        assert len(encoded) == 2
        assert 'Invalid' not in encoded['composition'].values

    def test_validate_periodic_descriptors_count(self):
        """
        Test that feature vectors include at least two periodic descriptors per element.
        """
        data = {
            'composition': ['Fe0.5Ni0.5'],
            'bulk_modulus': [100.0]
        }
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df)
        
        avg_cols = [c for c in encoded.columns if c.startswith('avg_')]
        var_cols = [c for c in encoded.columns if c.startswith('var_')]
        
        # We expect 10 avg and 10 var columns based on PERIODIC_PROPERTIES
        assert len(avg_cols) >= 2
        assert len(var_cols) >= 2

    def test_output_shape(self):
        data = {
            'composition': ['Fe0.5Ni0.5'] * 10,
            'bulk_modulus': [100.0] * 10
        }
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df)
        
        assert len(encoded) == 10
        # Check that all rows are identical
        assert encoded['frac_Fe'].iloc[0] == encoded['frac_Fe'].iloc[1]