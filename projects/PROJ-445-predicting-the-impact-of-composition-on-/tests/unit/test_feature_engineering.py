import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the feature engineering functions from the project's constants module
from src.utils.constants import (
    parse_composition,
    compute_mean_coordination_number,
    compute_electronegativity_variance,
    compute_atomic_radius_variance
)

class TestParseComposition:
    """Unit tests for parsing chemical compositions."""

    def test_parse_simple_binary(self):
        """Test parsing a simple binary composition like 'Ge20Se80'."""
        elements, ratios = parse_composition("Ge20Se80")
        assert elements == ["Ge", "Se"]
        assert ratios == [20, 80]
        assert abs(sum(ratios) - 100.0) < 1e-6

    def test_parse_ternary(self):
        """Test parsing a ternary composition like 'As10Ge30Se60'."""
        elements, ratios = parse_composition("As10Ge30Se60")
        assert elements == ["As", "Ge", "Se"]
        assert ratios == [10, 30, 60]
        assert abs(sum(ratios) - 100.0) < 1e-6

    def test_parse_with_floats(self):
        """Test parsing with float ratios."""
        elements, ratios = parse_composition("Sb5.5Ge22.5Se72")
        assert elements == ["Sb", "Ge", "Se"]
        assert abs(ratios[0] - 5.5) < 1e-6
        assert abs(ratios[1] - 22.5) < 1e-6
        assert abs(ratios[2] - 72.0) < 1e-6

    def test_parse_invalid_formula(self):
        """Test that invalid formulas raise ValueError."""
        with pytest.raises(ValueError):
            parse_composition("GeSe")  # Missing ratios
        with pytest.raises(ValueError):
            parse_composition("Ge20Se")  # Missing ratio for second element

class TestFeatureComputation:
    """Unit tests for feature engineering: MCN, electronegativity variance, atomic radius variance."""

    def test_mean_coordination_number_binary(self):
        """
        Test MCN for Ge20Se80.
        Ge (Group 14) has coordination number 4.
        Se (Group 16) has coordination number 2.
        MCN = 0.20 * 4 + 0.80 * 2 = 0.8 + 1.6 = 2.4
        """
        composition = "Ge20Se80"
        elements, ratios = parse_composition(composition)
        mcn = compute_mean_coordination_number(elements, ratios)
        expected_mcn = 0.20 * 4 + 0.80 * 2
        assert abs(mcn - expected_mcn) < 1e-6

    def test_mean_coordination_number_ternary(self):
        """
        Test MCN for As10Ge30Se60.
        As (Group 15) has coordination number 3.
        Ge (Group 14) has coordination number 4.
        Se (Group 16) has coordination number 2.
        MCN = 0.10 * 3 + 0.30 * 4 + 0.60 * 2 = 0.3 + 1.2 + 1.2 = 2.7
        """
        composition = "As10Ge30Se60"
        elements, ratios = parse_composition(composition)
        mcn = compute_mean_coordination_number(elements, ratios)
        expected_mcn = 0.10 * 3 + 0.30 * 4 + 0.60 * 2
        assert abs(mcn - expected_mcn) < 1e-6

    def test_electronegativity_variance_binary(self):
        """
        Test electronegativity variance for Ge20Se80.
        Values from mendeleev (Pauling scale approx):
        Ge ~ 2.01, Se ~ 2.55
        Mean EN = 0.20 * 2.01 + 0.80 * 2.55 = 0.402 + 2.04 = 2.442
        Var = 0.20 * (2.01 - 2.442)^2 + 0.80 * (2.55 - 2.442)^2
        """
        composition = "Ge20Se80"
        elements, ratios = parse_composition(composition)
        en_var = compute_electronegativity_variance(elements, ratios)
        
        # We just verify it's a non-negative number and not NaN
        assert isinstance(en_var, float)
        assert en_var >= 0
        assert not np.isnan(en_var)
        assert not np.isinf(en_var)

    def test_electronegativity_variance_ternary(self):
        """
        Test electronegativity variance for As10Ge30Se60.
        As ~ 2.18, Ge ~ 2.01, Se ~ 2.55
        """
        composition = "As10Ge30Se60"
        elements, ratios = parse_composition(composition)
        en_var = compute_electronegativity_variance(elements, ratios)
        
        assert isinstance(en_var, float)
        assert en_var >= 0
        assert not np.isnan(en_var)
        assert not np.isinf(en_var)

    def test_atomic_radius_variance_binary(self):
        """
        Test atomic radius variance for Ge20Se80.
        Uses covalent radii from mendeleev.
        """
        composition = "Ge20Se80"
        elements, ratios = parse_composition(composition)
        radius_var = compute_atomic_radius_variance(elements, ratios)
        
        assert isinstance(radius_var, float)
        assert radius_var >= 0
        assert not np.isnan(radius_var)
        assert not np.isinf(radius_var)

    def test_atomic_radius_variance_ternary(self):
        """
        Test atomic radius variance for As10Ge30Se60.
        """
        composition = "As10Ge30Se60"
        elements, ratios = parse_composition(composition)
        radius_var = compute_atomic_radius_variance(elements, ratios)
        
        assert isinstance(radius_var, float)
        assert radius_var >= 0
        assert not np.isnan(radius_var)
        assert not np.isinf(radius_var)

    def test_unknown_element_handling(self):
        """Test that unknown elements raise an error or return None."""
        # This test assumes the constants module raises an error for unknown elements
        # If the implementation returns None, adjust accordingly.
        # Based on the typical implementation using mendeleev, an unknown element
        # will raise a ValueError or return None.
        
        # We test with a hypothetical unknown element "Xx"
        # If the function handles it by raising:
        with pytest.raises((ValueError, TypeError)):
            # Note: 'Xx' is not a real element, so mendeleev should fail
            # If the implementation catches and returns None, this test should be adjusted.
            compute_mean_coordination_number(["Xx"], [100])

class TestIntegrationWithDataFrame:
    """Integration tests ensuring features work in a DataFrame context."""

    def test_compute_features_on_dataframe(self):
        """Test that feature functions can be applied to a pandas DataFrame."""
        df = pd.DataFrame({
            'composition': ['Ge20Se80', 'As10Ge30Se60', 'Sb5Ge25Se70'],
            'Tg': [200, 250, 300]
        })

        # Apply parsing
        parsed = df['composition'].apply(parse_composition)
        df['elements'] = parsed.apply(lambda x: x[0])
        df['ratios'] = parsed.apply(lambda x: x[1])

        # Apply feature engineering
        df['MCN'] = df.apply(
            lambda row: compute_mean_coordination_number(row['elements'], row['ratios']),
            axis=1
        )
        df['EN_Variance'] = df.apply(
            lambda row: compute_electronegativity_variance(row['elements'], row['ratios']),
            axis=1
        )
        df['Radius_Variance'] = df.apply(
            lambda row: compute_atomic_radius_variance(row['elements'], row['ratios']),
            axis=1
        )

        # Verify columns exist and are numeric
        assert 'MCN' in df.columns
        assert 'EN_Variance' in df.columns
        assert 'Radius_Variance' in df.columns
        assert df['MCN'].dtype in [np.float64, np.float32]
        assert df['EN_Variance'].dtype in [np.float64, np.float32]
        assert df['Radius_Variance'].dtype in [np.float64, np.float32]
        
        # Verify no NaN values were introduced (assuming all elements are valid)
        assert not df['MCN'].isna().any()
        assert not df['EN_Variance'].isna().any()
        assert not df['Radius_Variance'].isna().any()
        
        # Verify MCN values are within a reasonable range (typically 2.0 to 4.0 for chalcogenides)
        assert df['MCN'].min() >= 2.0
        assert df['MCN'].max() <= 4.5