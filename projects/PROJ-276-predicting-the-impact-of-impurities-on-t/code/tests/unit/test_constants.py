"""
Unit tests for the constants module.
"""

import pytest
import math
from code.src.utils import constants


class TestAtomicWeights:
    """Tests for atomic weight retrieval."""

    def test_get_mg_weight(self):
        """Test retrieving Magnesium atomic weight."""
        weight = constants.get_atomic_weight("Mg")
        assert isinstance(weight, float)
        assert 24.0 < weight < 25.0

    def test_get_b_weight(self):
        """Test retrieving Boron atomic weight."""
        weight = constants.get_atomic_weight("B")
        assert isinstance(weight, float)
        assert 10.0 < weight < 11.0

    def test_get_c_weight(self):
        """Test retrieving Carbon atomic weight."""
        weight = constants.get_atomic_weight("C")
        assert isinstance(weight, float)
        assert 12.0 < weight < 12.1

    def test_get_unknown_element(self):
        """Test that KeyError is raised for unknown element."""
        with pytest.raises(KeyError):
            constants.get_atomic_weight("Xx")

    def test_case_sensitivity(self):
        """Test that element lookup is case-sensitive."""
        with pytest.raises(KeyError):
            constants.get_atomic_weight("mg")  # lowercase should fail

class TestUnitConversions:
    """Tests for unit conversion constants."""

    def test_kelvin_to_celsius_constant(self):
        """Test Kelvin to Celsius conversion factor."""
        assert constants.KELVIN_TO_CELSIUS == 273.15

    def test_celsius_to_kelvin_constant(self):
        """Test Celsius to Kelvin conversion factor."""
        assert constants.CELSIUS_TO_KELVIN == 273.15

    def test_gpa_to_pa(self):
        """Test GPa to Pa conversion factor."""
        assert constants.GPA_TO_PA == 1e9

    def test_pa_to_gpa(self):
        """Test Pa to GPa conversion factor."""
        assert constants.PA_TO_GPA == 1e-9

    def test_gpa_to_bar(self):
        """Test GPa to bar conversion factor."""
        assert constants.GPA_TO_BAR == 10000

    def test_bar_to_gpa(self):
        """Test bar to GPa conversion factor."""
        assert constants.BAR_TO_GPA == 1e-4

class TestVIFThresholds:
    """Tests for VIF threshold constants."""

    def test_vif_threshold_value(self):
        """Test that VIF threshold is set to 5.0."""
        assert constants.VIF_THRESHOLD == 5.0

    def test_vif_threshold_type(self):
        """Test that VIF threshold is a float."""
        assert isinstance(constants.VIF_THRESHOLD, float)

class TestDataProcessingConstants:
    """Tests for data processing constants."""

    def test_null_value(self):
        """Test null value constant."""
        assert constants.NULL_VALUE is None

    def test_missing_indicator(self):
        """Test missing indicator value."""
        assert constants.MISSING_INDICATOR == -9999.0

class TestConstantsIntegrity:
    """Tests for overall constants module integrity."""

    def test_all_elements_have_weights(self):
        """Verify all elements in dictionary have valid weights."""
        for element, weight in constants.ATOMIC_WEIGHTS.items():
            assert isinstance(element, str)
            assert len(element) <= 2
            assert isinstance(weight, (int, float))
            assert weight > 0

    def test_conversion_factors_are_positive(self):
        """Verify all conversion factors are positive."""
        assert constants.KELVIN_TO_CELSIUS > 0
        assert constants.CELSIUS_TO_KELVIN > 0
        assert constants.GPA_TO_PA > 0
        assert constants.PA_TO_GPA > 0
        assert constants.GPA_TO_BAR > 0
        assert constants.BAR_TO_GPA > 0