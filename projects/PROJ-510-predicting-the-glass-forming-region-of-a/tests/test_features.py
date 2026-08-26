"""
Unit tests for feature engineering functions.
"""
import pytest
import numpy as np
import pandas as pd
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.features import (
    parse_composition,
    get_element_properties_safe,
    calculate_mixing_enthalpy,
    calculate_atomic_size_mismatch,
    calculate_electronegativity_variance,
    compute_features,
    validate_features
)

class TestParseComposition:
    def test_simple_binary(self):
        comp = parse_composition("Cu50Zr50")
        assert abs(comp['Cu'] - 0.5) < 1e-6
        assert abs(comp['Zr'] - 0.5) < 1e-6

    def test_ternary(self):
        comp = parse_composition("Cu60Zr30Al10")
        assert abs(comp['Cu'] - 0.6) < 1e-6
        assert abs(comp['Zr'] - 0.3) < 1e-6
        assert abs(comp['Al'] - 0.1) < 1e-6

    def test_underscore_format(self):
        comp = parse_composition("Cu_50_Zr_50")
        assert abs(comp['Cu'] - 0.5) < 1e-6
        assert abs(comp['Zr'] - 0.5) < 1e-6

    def test_invalid_element(self):
        with pytest.raises(ValueError):
            parse_composition("Xx99Yy1") # Xx is not a real element

class TestGetElementProperties:
    def test_valid_element(self):
        props = get_element_properties_safe("Cu")
        assert props is not None
        assert props['symbol'] == 'Cu'
        assert 'atomic_radius' in props
        assert 'electronegativity' in props

    def test_invalid_element(self):
        props = get_element_properties_safe("Xx")
        assert props is None

class TestCalculateMixingEnthalpy:
    def test_binary_alloy(self):
        # Cu-Zr
        comp = {'Cu': 0.5, 'Zr': 0.5}
        enthalpy = calculate_mixing_enthalpy(comp)
        # Should be a float, likely negative
        assert isinstance(enthalpy, float)
        assert not np.isnan(enthalpy)

    def test_single_element(self):
        comp = {'Cu': 1.0}
        enthalpy = calculate_mixing_enthalpy(comp)
        assert enthalpy == 0.0

class TestCalculateAtomicSizeMismatch:
    def test_binary_alloy(self):
        comp = {'Cu': 0.5, 'Zr': 0.5}
        mismatch = calculate_atomic_size_mismatch(comp)
        assert isinstance(mismatch, float)
        assert not np.isnan(mismatch)
        assert mismatch >= 0

class TestCalculateElectronegativityVariance:
    def test_binary_alloy(self):
        comp = {'Cu': 0.5, 'Zr': 0.5}
        variance = calculate_electronegativity_variance(comp)
        assert isinstance(variance, float)
        assert not np.isnan(variance)
        assert variance >= 0

class TestComputeFeatures:
    def test_dataframe_computation(self):
        data = {
            'composition': ['Cu50Zr50', 'Cu60Zr30Al10'],
            'critical_cooling_rate': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        result_df = compute_features(df)

        assert 'mixing_enthalpy' in result_df.columns
        assert 'atomic_size_mismatch' in result_df.columns
        assert 'electronegativity_variance' in result_df.columns
        assert len(result_df) == 2
        assert not result_df['mixing_enthalpy'].isna().all()

class TestValidateFeatures:
    def test_valid_dataframe(self):
        data = {
            'mixing_enthalpy': [1.0, 2.0],
            'atomic_size_mismatch': [5.0, 6.0],
            'electronegativity_variance': [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        assert validate_features(df) is True

    def test_missing_column(self):
        data = {
            'mixing_enthalpy': [1.0, 2.0]
        }
        df = pd.DataFrame(data)
        assert validate_features(df) is False
