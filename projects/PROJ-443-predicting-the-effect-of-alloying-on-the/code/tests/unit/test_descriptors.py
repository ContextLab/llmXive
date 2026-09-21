"""
Unit tests for descriptor calculation in src/features/descriptors.py.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.features.descriptors import (
    get_miedema_param,
    calculate_miedema_features,
    calculate_standard_descriptors,
    compute_descriptors,
    apply_ilr_transformation,
    get_descriptor_columns,
    MIEDEMA_PARAMETERS
)

class TestMiedemaParam:
    def test_get_miedema_param_n_ws(self):
        val = get_miedema_param('Fe', 'n_ws')
        assert val == 1.55
    
    def test_get_miedema_param_phi(self):
        val = get_miedema_param('Fe', 'phi')
        assert val == 1.83
    
    def test_get_miedema_param_r(self):
        val = get_miedema_param('Fe', 'r')
        assert val == 1.26
    
    def test_invalid_element(self):
        with pytest.raises(KeyError):
            get_miedema_param('X', 'phi')
    
    def test_invalid_param_type(self):
        with pytest.raises(ValueError):
            get_miedema_param('Fe', 'invalid')

class TestCalculateMiedemaFeatures:
    @pytest.fixture
    def sample_df(self):
        # Create a simple HEA composition: Fe50Ni50
        data = {
            'Fe': [0.5, 0.4],
            'Ni': [0.5, 0.6],
            'Cr': [0.0, 0.0],
            'c_Fe': [0.5, 0.4],
            'c_Ni': [0.5, 0.6],
            'c_Cr': [0.0, 0.0],
            'Bulk_Modulus_Observed': [180.0, 190.0]
        }
        return pd.DataFrame(data)
    
    def test_miedema_features_added(self, sample_df):
        result = calculate_miedema_features(sample_df)
        assert 'mixing_enthalpy_miedema' in result.columns
        assert 'atomic_radius_variance_miedema' in result.columns
        assert 'electronegativity_variance_miedema' in result.columns
    
    def test_miedema_features_values(self, sample_df):
        result = calculate_miedema_features(sample_df)
        # Check that values are numeric and not NaN
        assert not result['mixing_enthalpy_miedema'].isna().any()
        assert not result['atomic_radius_variance_miedema'].isna().any()
        assert not result['electronegativity_variance_miedema'].isna().any()
        # Fe50Ni50 should have some variance
        assert result['atomic_radius_variance_miedema'].iloc[0] >= 0
        assert result['electronegativity_variance_miedema'].iloc[0] >= 0
    
    def test_single_element_no_variance(self):
        # Single element: Fe100
        data = {
            'Fe': [1.0],
            'c_Fe': [1.0],
            'Bulk_Modulus_Observed': [180.0]
        }
        df = pd.DataFrame(data)
        result = calculate_miedema_features(df)
        # Variance should be 0 for single element
        assert result['atomic_radius_variance_miedema'].iloc[0] == 0.0
        assert result['electronegativity_variance_miedema'].iloc[0] == 0.0

class TestCalculateStandardDescriptors:
    @pytest.fixture
    def sample_df(self):
        data = {
            'Fe': [0.5, 0.2],
            'Ni': [0.5, 0.3],
            'Cr': [0.0, 0.5],
            'c_Fe': [0.5, 0.2],
            'c_Ni': [0.5, 0.3],
            'c_Cr': [0.0, 0.5],
            'Bulk_Modulus_Observed': [180.0, 190.0]
        }
        return pd.DataFrame(data)
    
    def test_standard_descriptors_added(self, sample_df):
        result = calculate_standard_descriptors(sample_df)
        assert 'delta_s_mix' in result.columns
        assert 'VEC' in result.columns
        assert 'delta' in result.columns
    
    def test_delta_s_mix_positive(self, sample_df):
        result = calculate_standard_descriptors(sample_df)
        # Entropy should be positive
        assert (result['delta_s_mix'] > 0).all()
    
    def test_VEC_calculation(self, sample_df):
        result = calculate_standard_descriptors(sample_df)
        # Fe (8), Ni (10), Cr (6)
        # Row 0: 0.5*8 + 0.5*10 = 9.0
        # Row 1: 0.2*8 + 0.3*10 + 0.5*6 = 1.6 + 3.0 + 3.0 = 7.6
        assert np.isclose(result['VEC'].iloc[0], 9.0)
        assert np.isclose(result['VEC'].iloc[1], 7.6)

class TestComputeDescriptors:
    @pytest.fixture
    def sample_df(self):
        data = {
            'Fe': [0.5],
            'Ni': [0.5],
            'c_Fe': [0.5],
            'c_Ni': [0.5],
            'Bulk_Modulus_Observed': [180.0]
        }
        return pd.DataFrame(data)
    
    def test_all_descriptors_computed(self, sample_df):
        result = compute_descriptors(sample_df)
        # Miedema features
        assert 'mixing_enthalpy_miedema' in result.columns
        assert 'atomic_radius_variance_miedema' in result.columns
        assert 'electronegativity_variance_miedema' in result.columns
        # Standard descriptors
        assert 'delta_s_mix' in result.columns
        assert 'VEC' in result.columns
        assert 'delta' in result.columns

class TestApplyILRTransformation:
    @pytest.fixture
    def sample_df(self):
        data = {
            'Fe': [0.5, 0.4],
            'Ni': [0.5, 0.6],
            'c_Fe': [0.5, 0.4],
            'c_Ni': [0.5, 0.6],
            'Bulk_Modulus_Observed': [180.0, 190.0]
        }
        return pd.DataFrame(data)
    
    def test_ilr_columns_added(self, sample_df):
        result = apply_ilr_transformation(sample_df)
        # ILR transformation should add columns (e.g., ilr_1, ilr_2, ...)
        # The exact names depend on the coda implementation
        # Check that new columns exist and are not just the original ones
        original_cols = set(sample_df.columns)
        new_cols = set(result.columns) - original_cols
        assert len(new_cols) > 0, "ILR transformation should add new columns"
    
    def test_no_nan_in_ilr(self, sample_df):
        result = apply_ilr_transformation(sample_df)
        # ILR columns should not have NaN
        ilr_cols = [c for c in result.columns if 'ilr' in c.lower()]
        for col in ilr_cols:
            assert not result[col].isna().any(), f"Column {col} has NaN values"

class TestGetDescriptorColumns:
    @pytest.fixture
    def sample_df(self):
        data = {
            'Fe': [0.5],
            'Ni': [0.5],
            'c_Fe': [0.5],
            'c_Ni': [0.5],
            'mixing_enthalpy_miedema': [10.0],
            'delta_s_mix': [5.0],
            'VEC': [9.0],
            'Bulk_Modulus_Observed': [180.0],
            'Bulk_Modulus_Residual': [10.0]
        }
        return pd.DataFrame(data)
    
    def test_excludes_composition(self, sample_df):
        cols = get_descriptor_columns(sample_df)
        assert 'Fe' not in cols
        assert 'Ni' not in cols
        assert 'c_Fe' not in cols
        assert 'c_Ni' not in cols
    
    def test_excludes_targets(self, sample_df):
        cols = get_descriptor_columns(sample_df)
        assert 'Bulk_Modulus_Observed' not in cols
        assert 'Bulk_Modulus_Residual' not in cols
    
    def test_includes_descriptors(self, sample_df):
        cols = get_descriptor_columns(sample_df)
        assert 'mixing_enthalpy_miedema' in cols
        assert 'delta_s_mix' in cols
        assert 'VEC' in cols