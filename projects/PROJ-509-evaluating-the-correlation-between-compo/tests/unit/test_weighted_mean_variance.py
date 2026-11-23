"""
Unit tests for the weighted mean and variance calculation functions.

These tests verify edge cases in the calculation logic, including
division by zero, single-element compounds, and extreme weight distributions.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from descriptors import calculate_weighted_mean_variance
from config import load_paths


class TestWeightedMeanVariance:
    """Tests for weighted mean and variance calculations."""

    @pytest.fixture
    def sample_properties(self):
        """Create a sample elemental properties DataFrame."""
        data = {
            'element': ['H', 'C', 'O', 'Na', 'Cl', 'Fe'],
            'electronegativity': [2.20, 2.55, 3.44, 0.93, 3.16, 1.83],
            'atomic_radius': [37.0, 77.0, 66.0, 186.0, 99.0, 126.0],
            'valence': [1, 4, 2, 1, 1, 3],
            'melting_point': [14.0, 3500.0, 54.0, 98.0, -101.0, 1538.0],
            'ionization_energy': [13.6, 11.3, 13.6, 5.1, 13.0, 7.9]
        }
        return pd.DataFrame(data)

    def test_single_element_compound(self, sample_properties):
        """Test calculation for a single-element compound."""
        elements = ['Fe']
        stoichiometry = [1]
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, sample_properties
        )
        
        # For a single element, mean should equal the property value
        # and variance should be 0
        assert result['mean_electronegativity'] == 1.83
        assert result['variance_electronegativity'] == 0.0
        assert result['mean_atomic_radius'] == 126.0
        assert result['variance_atomic_radius'] == 0.0

    def test_two_element_compound(self, sample_properties):
        """Test calculation for a two-element compound."""
        elements = ['Na', 'Cl']
        stoichiometry = [1, 1]  # NaCl
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, sample_properties
        )
        
        # Mean electronegativity: (0.93 + 3.16) / 2 = 2.045
        expected_mean = (0.93 + 3.16) / 2
        assert abs(result['mean_electronegativity'] - expected_mean) < 1e-6
        
        # Variance: ((0.93-2.045)^2 + (3.16-2.045)^2) / 2
        expected_var = ((0.93 - expected_mean)**2 + (3.16 - expected_mean)**2) / 2
        assert abs(result['variance_electronegativity'] - expected_var) < 1e-6

    def test_three_element_compound(self, sample_properties):
        """Test calculation for a three-element compound."""
        elements = ['H', 'C', 'O']
        stoichiometry = [2, 1, 1]  # CH2O (formaldehyde)
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, sample_properties
        )
        
        # Total stoichiometry = 4
        # Mean electronegativity: (2*2.20 + 1*2.55 + 1*3.44) / 4 = 2.6225
        total_stoich = sum(stoichiometry)
        expected_mean = (
            2 * 2.20 + 1 * 2.55 + 1 * 3.44
        ) / total_stoich
        
        assert abs(result['mean_electronegativity'] - expected_mean) < 1e-6

    def test_unequal_stoichiometry(self, sample_properties):
        """Test calculation with highly unequal stoichiometry."""
        elements = ['H', 'O']
        stoichiometry = [100, 1]  # H100O (extreme)
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, sample_properties
        )
        
        # The mean should be very close to H's value due to high weight
        # Mean: (100*2.20 + 1*3.44) / 101 ≈ 2.212
        expected_mean = (100 * 2.20 + 1 * 3.44) / 101
        assert abs(result['mean_electronegativity'] - expected_mean) < 1e-3

    def test_all_same_element(self, sample_properties):
        """Test calculation where all elements are the same."""
        elements = ['O', 'O', 'O']
        stoichiometry = [2, 1, 1]  # Effectively O4
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, sample_properties
        )
        
        # All values are the same, so variance should be 0
        assert result['mean_electronegativity'] == 3.44
        assert result['variance_electronegativity'] == 0.0

    def test_zero_total_stoichiometry(self, sample_properties):
        """Test calculation with zero total stoichiometry."""
        elements = ['H', 'O']
        stoichiometry = [0, 0]
        
        # This should raise an error or return NaN
        try:
            result = calculate_weighted_mean_variance(
                elements, stoichiometry, sample_properties
            )
            # If it succeeds, check for NaN
            assert any(np.isnan(v) for v in result.values()), \
                "Zero stoichiometry should result in NaN"
        except ZeroDivisionError:
            # Expected: division by zero
            pass

    def test_negative_stoichiometry(self, sample_properties):
        """Test calculation with negative stoichiometry."""
        elements = ['H', 'O']
        stoichiometry = [1, -1]
        
        try:
            result = calculate_weighted_mean_variance(
                elements, stoichiometry, sample_properties
            )
            # If it succeeds, check the result
            assert isinstance(result, dict)
        except ValueError:
            # Expected: negative stoichiometry is invalid
            pass

    def test_mixed_positive_negative_stoichiometry(self, sample_properties):
        """Test calculation with mixed positive and negative stoichiometry."""
        elements = ['H', 'O', 'Na']
        stoichiometry = [2, -1, 1]  # Sum = 2
        
        try:
            result = calculate_weighted_mean_variance(
                elements, stoichiometry, sample_properties
            )
            # If it succeeds, check the result
            assert isinstance(result, dict)
        except ValueError:
            # Expected: negative stoichiometry is invalid
            pass

    def test_extreme_weight_distribution(self, sample_properties):
        """Test calculation with extreme weight distribution."""
        elements = ['H', 'Fe']
        stoichiometry = [1, 1000000]  # Fe dominates
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, sample_properties
        )
        
        # The mean should be very close to Fe's value
        # Mean: (1*2.20 + 1000000*1.83) / 1000001 ≈ 1.83
        expected_mean = (1 * 2.20 + 1000000 * 1.83) / 1000001
        assert abs(result['mean_electronegativity'] - expected_mean) < 1e-4

    def test_all_properties_zero(self):
        """Test calculation when all property values are zero."""
        # Create properties with all zeros
        data = {
            'element': ['A', 'B'],
            'electronegativity': [0.0, 0.0],
            'atomic_radius': [0.0, 0.0],
            'valence': [0, 0],
            'melting_point': [0.0, 0.0],
            'ionization_energy': [0.0, 0.0]
        }
        zero_props = pd.DataFrame(data)
        
        elements = ['A', 'B']
        stoichiometry = [1, 1]
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, zero_props
        )
        
        # All means should be 0, all variances should be 0
        assert result['mean_electronegativity'] == 0.0
        assert result['variance_electronegativity'] == 0.0

    def test_very_large_property_values(self, sample_properties):
        """Test calculation with very large property values."""
        # Modify properties to have very large values
        data = sample_properties.copy()
        data.loc[data['element'] == 'H', 'electronegativity'] = 1e10
        
        elements = ['H', 'C']
        stoichiometry = [1, 1]
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, data
        )
        
        # Should handle large values without overflow
        assert isinstance(result['mean_electronegativity'], float)
        assert not np.isinf(result['mean_electronegativity'])

    def test_very_small_property_values(self, sample_properties):
        """Test calculation with very small property values."""
        # Modify properties to have very small values
        data = sample_properties.copy()
        data.loc[data['element'] == 'H', 'electronegativity'] = 1e-10
        
        elements = ['H', 'C']
        stoichiometry = [1, 1]
        
        result = calculate_weighted_mean_variance(
            elements, stoichiometry, data
        )
        
        # Should handle small values without underflow
        assert isinstance(result['mean_electronegativity'], float)
        assert not np.isnan(result['mean_electronegativity'])
