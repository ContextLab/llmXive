"""
Unit tests for descriptor calculation module.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.features.descriptors import (
    get_miedema_param,
    calculate_miedema_features,
    calculate_standard_descriptors,
    compute_descriptors,
    apply_ilr_transformation,
    get_descriptor_columns
)


class TestMiedemaParam:
    def test_get_phi(self):
        assert get_miedema_param('Fe', 'phi') == 4.2
        assert get_miedema_param('Ni', 'phi') == 4.4

    def test_get_radius(self):
        assert get_miedema_param('Fe', 'radius') == 126
        assert get_miedema_param('Ni', 'radius') == 124

    def test_get_unknown_element(self):
        assert get_miedema_param('Unknown', 'phi') == 0.0

    def test_get_unknown_param_type(self):
        assert get_miedema_param('Fe', 'unknown') == 0.0


class TestCalculateMiedemaFeatures:
    def test_basic_computation(self):
        row = {'Fe': 0.5, 'Ni': 0.5}
        features = calculate_miedema_features(row)
        
        assert 'mixing_enthalpy_miedema' in features
        assert 'atomic_radius_variance_miedema' in features
        assert 'electronegativity_variance_miedema' in features
        
        # Fe and Ni have very similar properties, so variance should be low
        assert features['atomic_radius_variance_miedema'] < 1.0
        assert features['electronegativity_variance_miedema'] < 0.01

    def test_empty_composition(self):
        row = {}
        features = calculate_miedema_features(row)
        
        assert features['mixing_enthalpy_miedema'] == 0.0
        assert features['atomic_radius_variance_miedema'] == 0.0
        assert features['electronegativity_variance_miedema'] == 0.0

    def test_single_element(self):
        row = {'Fe': 1.0}
        features = calculate_miedema_features(row)
        
        # Single element should have zero variance
        assert features['atomic_radius_variance_miedema'] == 0.0
        assert features['electronegativity_variance_miedema'] == 0.0


class TestCalculateStandardDescriptors:
    def test_entropy_calculation(self):
        # Equimolar FeCoNi -> S_mix = R * ln(3)
        row = {'Fe': 0.333, 'Co': 0.333, 'Ni': 0.334}
        features = calculate_standard_descriptors(row)
        
        assert 'configurational_entropy' in features
        assert features['configurational_entropy'] > 0
        
        # Approximate check: R * ln(3) = 8.314 * 1.0986 = 9.13
        assert 8.0 < features['configurational_entropy'] < 10.0

    def test_vec_calculation(self):
        row = {'Fe': 0.5, 'Ni': 0.5}
        features = calculate_standard_descriptors(row)
        
        assert 'valence_electron_concentration' in features
        # Fe(8) and Ni(10) -> avg = 9
        assert 8.0 < features['valence_electron_concentration'] < 10.0

    def test_atomic_size_difference(self):
        row = {'Fe': 0.5, 'Ni': 0.5}
        features = calculate_standard_descriptors(row)
        
        assert 'atomic_size_difference' in features
        # Fe and Ni have similar radii, so delta should be small
        assert features['atomic_size_difference'] < 5.0


class TestComputeDescriptors:
    def test_dataframe_processing(self):
        df = pd.DataFrame({
            'Fe': [0.5, 0.3],
            'Ni': [0.5, 0.3],
            'Cr': [0.0, 0.4]
        })
        
        result = compute_descriptors(df)
        
        assert 'mixing_enthalpy_miedema' in result.columns
        assert 'configurational_entropy' in result.columns
        assert len(result) == 2

    def test_mixed_elements(self):
        df = pd.DataFrame({
            'Al': [0.2],
            'Co': [0.2],
            'Cr': [0.2],
            'Fe': [0.2],
            'Ni': [0.2]
        })
        
        result = compute_descriptors(df)
        
        # Check that all Miedema features are present
        assert 'mixing_enthalpy_miedema' in result.columns
        assert 'atomic_radius_variance_miedema' in result.columns
        assert 'electronegativity_variance_miedema' in result.columns
        
        # Check that all standard features are present
        assert 'configurational_entropy' in result.columns
        assert 'valence_electron_concentration' in result.columns
        assert 'atomic_size_difference' in result.columns


class TestApplyILRTransformation:
    def test_ilr_transformation(self):
        df = pd.DataFrame({
            'Fe': [0.5, 0.4],
            'Ni': [0.5, 0.3],
            'Cr': [0.0, 0.3]
        })
        
        result = apply_ilr_transformation(df, ['Fe', 'Ni', 'Cr'])
        
        # Check that ILR columns are added
        assert any(col.startswith('ilr_') for col in result.columns)
        assert len(result.columns) > len(df.columns)

    def test_insufficient_columns(self):
        df = pd.DataFrame({
            'Fe': [0.5]
        })
        
        result = apply_ilr_transformation(df, ['Fe'])
        
        # Should not add any ILR columns
        assert not any(col.startswith('ilr_') for col in result.columns)


class TestGetDescriptorColumns:
    def test_get_descriptor_names(self):
        df = pd.DataFrame({
            'Fe': [0.5],
            'mixing_enthalpy_miedema': [1.0],
            'configurational_entropy': [2.0],
            'other_column': [3.0]
        })
        
        cols = get_descriptor_columns(df)
        
        assert 'mixing_enthalpy_miedema' in cols
        assert 'configurational_entropy' in cols
        assert 'other_column' not in cols
        assert 'Fe' not in cols