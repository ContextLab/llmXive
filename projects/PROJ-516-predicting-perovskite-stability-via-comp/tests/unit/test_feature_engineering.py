"""
Unit tests for feature engineering module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from feature_engineering import (
    get_element_property,
    compute_composition_descriptors,
    load_raw_data,
    compute_descriptors
)
from utils.formula_parser import parse_formula, assign_perovskite_sites


class TestGetElementProperty:
    """Tests for get_element_property function."""

    def test_electronegativity_lead(self):
        val = get_element_property('Pb', 'electronegativity')
        assert val is not None
        assert 2.0 < val < 2.5  # Pb is approx 2.33

    def test_ionic_radius_iodine(self):
        val = get_element_property('I', 'ionic_radius')
        assert val is not None
        assert val > 0

    def test_first_ionization_energy(self):
        val = get_element_property('Na', 'first_ionization_energy')
        assert val is not None
        assert val > 0

    def test_unknown_element(self):
        val = get_element_property('Xx', 'electronegativity')
        assert val is None

    def test_invalid_property(self):
        with pytest.raises(ValueError):
            get_element_property('Pb', 'unknown_prop')


class TestComputeCompositionDescriptors:
    """Tests for compute_composition_descriptors function."""

    def test_simple_formula(self):
        # Test with a simple known formula
        sites = assign_perovskite_sites(parse_formula('CsPbI3'))
        avg, var = compute_composition_descriptors('CsPbI3', 'electronegativity', sites)
        
        assert avg is not None
        assert var is not None
        assert isinstance(avg, float)
        assert isinstance(var, float)

    def test_missing_property(self):
        # Create a mock site assignment with an element that might be missing
        # (though our dicts cover most common ones)
        sites = {'A': [('Cs', 1.0)], 'B': [('Pb', 1.0)], 'X': [('I', 3.0)]}
        avg, var = compute_composition_descriptors('CsPbI3', 'formation_enthalpy', sites)
        # Formation enthalpy for elements is 0.0 in our dict, so it should work
        assert avg == 0.0
        assert var == 0.0

    def test_variance_calculation(self):
        # If all elements have same property value, variance should be 0
        # Using 'formation_enthalpy' which is 0 for all elements in our dict
        sites = assign_perovskite_sites(parse_formula('CsPbI3'))
        avg, var = compute_composition_descriptors('CsPbI3', 'formation_enthalpy', sites)
        assert abs(var) < 1e-10  # Should be effectively zero


class TestLoadRawData:
    """Tests for load_raw_data function."""

    def test_missing_file_raises(self):
        # Temporarily rename the file if it exists to test error handling
        input_path = Path("data/raw/perovskites_merged.csv")
        backup_path = Path("data/raw/perovskites_merged.csv.bak")
        
        if input_path.exists():
            input_path.rename(backup_path)
        
        try:
            with pytest.raises(FileNotFoundError):
                load_raw_data()
        finally:
            if backup_path.exists():
                backup_path.rename(input_path)


class TestComputeDescriptors:
    """Tests for compute_descriptors function."""

    def test_descriptors_added(self):
        # Create a minimal test DataFrame
        data = {
            'formula': ['CsPbI3', 'MAPbI3'],
            'source': ['NREL', 'MP']
        }
        df = pd.DataFrame(data)
        
        result = compute_descriptors(df)
        
        # Check that required columns are added
        required_cols = [
            'weighted_ionic_radius',
            'weighted_ionic_radius_var',
            'weighted_electronegativity',
            'weighted_electronegativity_var',
            'weighted_formation_enthalpy',
            'weighted_formation_enthalpy_var',
            'weighted_first_ionization_energy',
            'weighted_first_ionization_energy_var',
            'atomic_fraction_A',
            'atomic_fraction_B',
            'atomic_fraction_X'
        ]
        
        for col in required_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_non_null_values(self):
        # Test that we get non-null values for known perovskites
        data = {
            'formula': ['CsPbI3', 'FAPbI3', 'MAPbI3'],
            'source': ['NREL', 'MP', 'NREL']
        }
        df = pd.DataFrame(data)
        
        result = compute_descriptors(df)
        
        # Check that we have non-null values for first ionization energy
        non_null = result['weighted_first_ionization_energy'].notna().sum()
        assert non_null > 0, "Expected non-null values for weighted_first_ionization_energy"

    def test_invalid_formula_handling(self):
        # Test that invalid formulas don't crash the pipeline
        data = {
            'formula': ['CsPbI3', 'InvalidFormula', 'MAPbI3'],
            'source': ['NREL', 'NREL', 'MP']
        }
        df = pd.DataFrame(data)
        
        # Should not raise an exception
        result = compute_descriptors(df)
        
        # Check that valid formulas have values
        assert result.loc[result['formula'] == 'CsPbI3', 'weighted_first_ionization_energy'].notna().iloc[0]
        assert result.loc[result['formula'] == 'MAPbI3', 'weighted_first_ionization_energy'].notna().iloc[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])