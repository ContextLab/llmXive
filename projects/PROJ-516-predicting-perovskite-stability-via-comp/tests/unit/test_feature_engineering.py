"""
Unit tests for feature_engineering.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the functions to test
from feature_engineering import (
    compute_composition_descriptors,
    compute_descriptors,
    load_raw_data,
    get_element_property
)

class TestGetElementProperty:
    def test_electronegativity_exists(self):
        val = get_element_property('Cs', 'electronegativity')
        assert not np.isnan(val), "Electronegativity should be available for Cs"

    def test_first_ionization_exists(self):
        val = get_element_property('I', 'first_ionization_energy')
        assert not np.isnan(val), "First ionization energy should be available for I"

class TestComputeCompositionDescriptors:
    def test_cs_pbi3_descriptors(self):
        """Test with a known perovskite: CsPbI3"""
        desc = compute_composition_descriptors("CsPbI3")

        assert 'formula' in desc
        assert desc['formula'] == "CsPbI3"
        assert 'num_elements' in desc
        assert desc['num_elements'] == 3

        # Check weighted averages exist
        assert 'weighted_ionic_radius' in desc
        assert 'weighted_electronegativity' in desc
        assert 'weighted_first_ionization_energy' in desc

        # Check variances exist
        assert 'variance_ionic_radius' in desc
        assert 'variance_electronegativity' in desc
        assert 'variance_first_ionization_energy' in desc

        # Check atomic fractions
        assert 'atomic_fraction_Cs' in desc
        assert 'atomic_fraction_Pb' in desc
        assert 'atomic_fraction_I' in desc

        # Verify fractions sum to 1 (approximately)
        total_frac = (desc['atomic_fraction_Cs'] +
                      desc['atomic_fraction_Pb'] +
                      desc['atomic_fraction_I'])
        assert np.isclose(total_frac, 1.0), "Atomic fractions should sum to 1"

    def test_missing_formula(self):
        desc = compute_composition_descriptors("InvalidFormula")
        # Should not crash, but return NaNs
        assert 'formula' in desc
        assert desc['formula'] == "InvalidFormula"

class TestComputeDescriptorsIntegration:
    def test_compute_descriptors_on_dataframe(self):
        # Create a small mock dataframe
        data = {
            'formula': ['CsPbI3', 'FAPbI3', 'MAPbBr3'],
            'T_d': [300, 310, 320]
        }
        df = pd.DataFrame(data)

        result = compute_descriptors(df)

        assert len(result) == 3
        assert 'formula' in result.columns
        assert 'weighted_electronegativity' in result.columns
        assert 'variance_ionic_radius' in result.columns
        assert 'atomic_fraction_Cs' in result.columns or 'atomic_fraction_Fa' in result.columns or 'atomic_fraction_Ma' in result.columns
        # Note: Fa and Ma are not standard elements, so they might be NaN or missing
        # The function should handle them gracefully (return NaN)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])