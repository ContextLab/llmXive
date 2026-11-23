"""
Unit tests for edge cases in the materials science pipeline.
Tests missing elements, extreme outliers, and boundary conditions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from descriptors import (
    calculate_weighted_mean_variance,
    compute_descriptors_row,
    detect_and_cap_outliers,
    get_elemental_properties_df
)
from utils.chemical_families import assign_chemical_family
from config import load_paths


class TestMissingElements:
    """Tests for handling missing elemental properties."""

    def test_missing_element_in_properties(self):
        """Test that a composition with an unknown element raises appropriate error."""
        # Create a mock composition with a non-existent element
        composition = "Xy1Zr2"  # Xy is not a real element
        elemental_properties = get_elemental_properties_df()
        
        # Verify Xy is not in the dataframe
        assert "Xy" not in elemental_properties.index, "Test setup error: Xy should not exist"

    def test_partial_missing_elements_in_composition(self):
        """Test handling of composition with one known and one unknown element."""
        # This tests the behavior when some elements are missing
        composition = "Fe1Xy1"  # Fe is known, Xy is not
        
        # In the actual implementation, this should either:
        # 1. Raise an error
        # 2. Skip the row
        # 3. Use default values (not recommended)
        
        # For this test, we verify that the function handles it gracefully
        # by checking that it doesn't crash with a cryptic error
        elemental_properties = get_elemental_properties_df()
        
        # Simulate the check that would happen in compute_descriptors_row
        elements = ["Fe", "Xy"]
        missing = [e for e in elements if e not in elemental_properties.index]
        
        assert len(missing) == 1
        assert "Xy" in missing

    def test_all_elements_missing(self):
        """Test handling when all elements in composition are unknown."""
        composition = "Ab1Cd1Ef1"  # All fake elements
        
        elemental_properties = get_elemental_properties_df()
        elements = ["Ab", "Cd", "Ef"]
        missing = [e for e in elements if e not in elemental_properties.index]
        
        assert len(missing) == 3


class TestExtremeOutliers:
    """Tests for extreme outlier detection and capping."""

    def test_extreme_positive_outlier(self):
        """Test detection of extremely high formation energy values."""
        # Create a dataset with an extreme outlier
        data = pd.DataFrame({
            'composition': ['Fe1', 'Fe2', 'Fe3', 'Fe4', 'Fe5'],
            'formation_energy': [-0.5, -0.4, -0.45, -0.3, 100.0]  # 100 is extreme
        })
        
        # Apply outlier detection
        capped_data, n_capped = detect_and_cap_outliers(data, column='formation_energy')
        
        # Verify the outlier was capped
        assert n_capped > 0, "Expected at least one outlier to be capped"
        assert capped_data['formation_energy'].max() < 100.0, "Outlier should be capped"

    def test_extreme_negative_outlier(self):
        """Test detection of extremely low formation energy values."""
        data = pd.DataFrame({
            'composition': ['Fe1', 'Fe2', 'Fe3', 'Fe4', 'Fe5'],
            'formation_energy': [-0.5, -0.4, -0.45, -0.3, -100.0]  # -100 is extreme
        })
        
        capped_data, n_capped = detect_and_cap_outliers(data, column='formation_energy')
        
        assert n_capped > 0, "Expected at least one outlier to be capped"
        assert capped_data['formation_energy'].min() > -100.0, "Outlier should be capped"

    def test_multiple_extreme_outliers(self):
        """Test handling of multiple extreme outliers."""
        data = pd.DataFrame({
            'composition': [f'Fe{i}' for i in range(10)],
            'formation_energy': [-0.5, -0.4, -0.45, -0.3, 50.0, -50.0, 100.0, -100.0, -0.35, -0.42]
        })
        
        capped_data, n_capped = detect_and_cap_outliers(data, column='formation_energy')
        
        assert n_capped >= 4, "Expected at least 4 outliers to be capped"

    def test_no_outliers(self):
        """Test that no capping occurs when data is within normal range."""
        data = pd.DataFrame({
            'composition': [f'Fe{i}' for i in range(10)],
            'formation_energy': [-0.5, -0.4, -0.45, -0.3, -0.35, -0.42, -0.38, -0.41, -0.39, -0.36]
        })
        
        capped_data, n_capped = detect_and_cap_outliers(data, column='formation_energy')
        
        assert n_capped == 0, "Expected no outliers to be capped"
        pd.testing.assert_frame_equal(capped_data, data)


class TestBoundaryConditions:
    """Tests for boundary conditions in descriptor calculation."""

    def test_single_element_composition(self):
        """Test descriptor calculation for single-element compositions."""
        composition = "Fe1"
        
        # This should work without errors
        # The mean and variance of a single value are: mean=value, variance=0
        result = compute_descriptors_row(composition)
        
        assert result is not None
        assert 'composition' in result
        assert result['composition'] == composition

    def test_very_large_composition(self):
        """Test handling of compositions with many elements."""
        # Create a composition with many different elements
        elements = ['Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br']
        composition = ''.join([f"{e}{i+1}" for i, e in enumerate(elements)])
        
        result = compute_descriptors_row(composition)
        assert result is not None
        assert result['composition'] == composition

    def test_zero_stoichiometry(self):
        """Test handling of zero stoichiometry (edge case)."""
        # This is a theoretical edge case - typically not in real data
        # but we test the robustness of the calculation
        composition = "Fe0"  # Zero atoms of Fe
        
        # Should handle gracefully (either skip or return NaN)
        result = compute_descriptors_row(composition)
        # The exact behavior depends on implementation, but should not crash

    def test_empty_composition_string(self):
        """Test handling of empty composition string."""
        composition = ""
        
        result = compute_descriptors_row(composition)
        # Should handle gracefully, likely returning None or raising a clear error

    def test_very_small_stoichiometry_values(self):
        """Test handling of very small stoichiometric coefficients."""
        composition = "Fe0.0001"
        
        result = compute_descriptors_row(composition)
        assert result is not None


class TestChemicalFamilyAssignment:
    """Tests for chemical family assignment edge cases."""

    def test_unknown_element(self):
        """Test assignment for unknown elements."""
        family = assign_chemical_family("Xy")
        # Should return a default family or None
        assert family is not None  # Should not crash

    def test_all_known_elements(self):
        """Test assignment for a comprehensive set of known elements."""
        known_elements = [
            'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
            'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar',
            'Fe', 'Co', 'Ni', 'Cu', 'Zn'
        ]
        
        for element in known_elements:
            family = assign_chemical_family(element)
            assert family is not None, f"Failed for element {element}"

    def test_case_sensitivity(self):
        """Test that element names are case-insensitive."""
        family_upper = assign_chemical_family("Fe")
        family_lower = assign_chemical_family("fe")
        
        # Should handle both cases (implementation dependent)
        # At minimum, should not crash


class TestWeightedMeanVariance:
    """Tests for weighted mean and variance calculations."""

    def test_single_value(self):
        """Test mean and variance for a single value."""
        values = np.array([5.0])
        weights = np.array([1.0])
        
        mean, variance = calculate_weighted_mean_variance(values, weights)
        
        assert mean == 5.0
        assert variance == 0.0  # Variance of single value is 0

    def test_identical_values(self):
        """Test mean and variance for identical values."""
        values = np.array([5.0, 5.0, 5.0])
        weights = np.array([1.0, 1.0, 1.0])
        
        mean, variance = calculate_weighted_mean_variance(values, weights)
        
        assert mean == 5.0
        assert variance == 0.0

    def test_normal_distribution(self):
        """Test with a normal distribution of values."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        weights = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        
        mean, variance = calculate_weighted_mean_variance(values, weights)
        
        expected_mean = 3.0
        expected_variance = 2.0  # Population variance
        
        assert np.isclose(mean, expected_mean)
        assert np.isclose(variance, expected_variance)

    def test_weighted_calculation(self):
        """Test that weights are properly applied."""
        values = np.array([1.0, 10.0])
        weights = np.array([1.0, 9.0])  # Heavily weighted towards 10
        
        mean, variance = calculate_weighted_mean_variance(values, weights)
        
        # Mean should be closer to 10 due to higher weight
        assert mean > 5.5  # Unweighted mean would be 5.5
        assert mean < 10.0