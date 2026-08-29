"""
Unit tests for feature engineering functions.
"""

import pytest
import pandas as pd
import numpy as np
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
    def test_valid_composition(self):
        """Test parsing a valid composition string."""
        comp = parse_composition("Cu50Zr40Al10")
        assert len(comp) == 3
        assert ('Cu', 50.0) in comp
        assert ('Zr', 40.0) in comp
        assert ('Al', 10.0) in comp
        
    def test_invalid_composition(self):
        """Test parsing an invalid composition string."""
        with pytest.raises(ValueError):
            parse_composition("InvalidComposition")
            
    def test_empty_composition(self):
        """Test parsing an empty composition string."""
        with pytest.raises(ValueError):
            parse_composition("")
            
    def test_float_fractions(self):
        """Test parsing with float fractions."""
        comp = parse_composition("Fe33.3Ni33.3Cr33.4")
        assert len(comp) == 3
        assert ('Fe', 33.3) in comp

class TestGetElementProperties:
    def test_known_element(self):
        """Test getting properties for a known element."""
        props = get_element_properties_safe("Cu")
        assert props['symbol'] == "Cu"
        assert props['atomic_mass'] is not None
        assert props['electronegativity'] is not None
        assert props['atomic_radius'] is not None
        
    def test_unknown_element(self):
        """Test getting properties for an unknown element."""
        with pytest.raises(ValueError):
            get_element_properties_safe("Xx")
            
    def test_case_sensitivity(self):
        """Test that element symbols are case-sensitive."""
        with pytest.raises(ValueError):
            get_element_properties_safe("cu")  # lowercase

class TestCalculateMixingEnthalpy:
    def test_simple_binary(self):
        """Test mixing enthalpy for a binary alloy."""
        composition = [("Cu", 0.5), ("Zr", 0.5)]
        props = {
            "Cu": {"electronegativity": 1.9, "atomic_radius": 128},
            "Zr": {"electronegativity": 1.33, "atomic_radius": 160}
        }
        h_mix = calculate_mixing_enthalpy(composition, props)
        assert isinstance(h_mix, float)
        # Should be negative for typical glass-forming alloys
        assert h_mix < 0
        
    def test_single_element(self):
        """Test mixing enthalpy for single element (should be 0)."""
        composition = [("Cu", 1.0)]
        props = {"Cu": {"electronegativity": 1.9, "atomic_radius": 128}}
        h_mix = calculate_mixing_enthalpy(composition, props)
        assert h_mix == 0.0

class TestCalculateAtomicSizeMismatch:
    def test_simple_binary(self):
        """Test atomic size mismatch for a binary alloy."""
        composition = [("Cu", 0.5), ("Zr", 0.5)]
        props = {
            "Cu": {"atomic_radius": 128},
            "Zr": {"atomic_radius": 160}
        }
        delta = calculate_atomic_size_mismatch(composition, props)
        assert isinstance(delta, float)
        assert delta > 0
        
    def test_identical_radii(self):
        """Test atomic size mismatch when radii are identical."""
        composition = [("Cu", 0.5), ("Cu", 0.5)]
        props = {"Cu": {"atomic_radius": 128}}
        delta = calculate_atomic_size_mismatch(composition, props)
        assert delta == 0.0

class TestCalculateElectronegativityVariance:
    def test_simple_binary(self):
        """Test electronegativity variance for a binary alloy."""
        composition = [("Cu", 0.5), ("Zr", 0.5)]
        props = {
            "Cu": {"electronegativity": 1.9},
            "Zr": {"electronegativity": 1.33}
        }
        chi_var = calculate_electronegativity_variance(composition, props)
        assert isinstance(chi_var, float)
        assert chi_var > 0
        
    def test_identical_electronegativity(self):
        """Test variance when electronegativities are identical."""
        composition = [("Cu", 0.5), ("Cu", 0.5)]
        props = {"Cu": {"electronegativity": 1.9}}
        chi_var = calculate_electronegativity_variance(composition, props)
        assert chi_var == 0.0

class TestComputeFeatures:
    def test_dataframe_processing(self):
        """Test computing features on a DataFrame."""
        df = pd.DataFrame({
            'composition': ['Cu50Zr40Al10', 'Fe33Ni33Cr34', 'Pd40Ni40P20']
        })
        df_result = compute_features(df)
        
        assert 'mixing_enthalpy' in df_result.columns
        assert 'atomic_size_mismatch' in df_result.columns
        assert 'electronegativity_variance' in df_result.columns
        assert len(df_result) == 3
        assert not df_result['mixing_enthalpy'].isna().any()
        assert not df_result['atomic_size_mismatch'].isna().any()
        assert not df_result['electronegativity_variance'].isna().any()
        
    def test_missing_composition_column(self):
        """Test error when composition column is missing."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        with pytest.raises(ValueError):
            compute_features(df)
            
    def test_invalid_composition_handling(self):
        """Test handling of invalid compositions."""
        df = pd.DataFrame({
            'composition': ['Cu50Zr40Al10', 'Invalid', 'Fe33Ni33Cr34']
        })
        df_result = compute_features(df)
        # Should have NaN for invalid composition
        assert df_result.loc[1, 'mixing_enthalpy'] != df_result.loc[1, 'mixing_enthalpy']  # NaN check

class TestValidateFeatures:
    def test_valid_features(self):
        """Test validation of valid features."""
        df = pd.DataFrame({
            'mixing_enthalpy': [-10.0, -15.0, -20.0],
            'atomic_size_mismatch': [0.1, 0.15, 0.2],
            'electronegativity_variance': [0.05, 0.08, 0.1]
        })
        assert validate_features(df) is True
        
    def test_missing_column(self):
        """Test validation fails with missing column."""
        df = pd.DataFrame({
            'mixing_enthalpy': [-10.0, -15.0, -20.0],
            'atomic_size_mismatch': [0.1, 0.15, 0.2]
        })
        with pytest.raises(ValueError):
            validate_features(df)
            
    def test_nan_values(self):
        """Test validation fails with NaN values."""
        df = pd.DataFrame({
            'mixing_enthalpy': [-10.0, np.nan, -20.0],
            'atomic_size_mismatch': [0.1, 0.15, 0.2],
            'electronegativity_variance': [0.05, 0.08, 0.1]
        })
        with pytest.raises(ValueError):
            validate_features(df)
            
    def test_zero_variance(self):
        """Test validation fails with zero variance."""
        df = pd.DataFrame({
            'mixing_enthalpy': [-10.0, -10.0, -10.0],
            'atomic_size_mismatch': [0.1, 0.15, 0.2],
            'electronegativity_variance': [0.05, 0.08, 0.1]
        })
        with pytest.raises(ValueError):
            validate_features(df)
