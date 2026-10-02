"""
Unit tests for the constants module.
"""
import pytest
import math
from code.src.utils import constants


class TestAtomicWeights:
    """Tests for atomic weight retrieval functionality."""

    def test_mg_atomic_weight(self):
        """Verify Magnesium atomic weight."""
        weight = constants.get_atomic_weight('Mg')
        assert abs(weight - 24.305) < 0.001

    def test_b_atomic_weight(self):
        """Verify Boron atomic weight."""
        weight = constants.get_atomic_weight('B')
        assert abs(weight - 10.81) < 0.001

    def test_c_atomic_weight(self):
        """Verify Carbon atomic weight."""
        weight = constants.get_atomic_weight('C')
        assert abs(weight - 12.011) < 0.001

    def test_invalid_element(self):
        """Verify KeyError is raised for invalid element."""
        with pytest.raises(KeyError):
            constants.get_atomic_weight('X')

    def test_case_sensitivity(self):
        """Verify element names are case-sensitive."""
        with pytest.raises(KeyError):
            constants.get_atomic_weight('mg')


class TestUnitConversions:
    """Tests for unit conversion factors."""

    def test_kelvin_to_celsius(self):
        """Verify Kelvin to Celsius conversion factor."""
        assert constants.KELVIN_TO_CELSIUS == 273.15

    def test_celsius_to_kelvin(self):
        """Verify Celsius to Kelvin conversion factor."""
        assert constants.CELSIUS_TO_KELVIN == 273.15

    def test_gpa_to_pa(self):
        """Verify GPa to Pa conversion factor."""
        assert constants.GPA_TO_PA == 1e9

    def test_pa_to_gpa(self):
        """Verify Pa to GPa conversion factor."""
        assert constants.PA_TO_GPA == 1e-9

    def test_mev_to_ev(self):
        """Verify MeV to eV conversion factor."""
        assert constants.MEV_TO_EV == 1e6

    def test_ev_to_mev(self):
        """Verify eV to MeV conversion factor."""
        assert constants.EV_TO_MEV == 1e-6


class TestVIFThresholds:
    """Tests for VIF threshold constants."""

    def test_vif_threshold_low(self):
        """Verify low VIF threshold value."""
        assert constants.VIF_THRESHOLD_LOW == 5.0

    def test_vif_threshold_high(self):
        """Verify high VIF threshold value."""
        assert constants.VIF_THRESHOLD_HIGH == 10.0


class TestDataProcessingConstants:
    """Tests for data processing constants."""

    def test_synthesis_range_default(self):
        """Verify default synthesis range uncertainty."""
        assert constants.SYNTHESIS_RANGE_DEFAULT == 0.05

    def test_null_value_threshold(self):
        """Verify null value percentage threshold."""
        assert constants.NULL_VALUE_THRESHOLD == 0.5


class TestConstantsIntegrity:
    """Tests for overall constants module integrity."""

    def test_all_elements_present(self):
        """Verify all common elements are in the database."""
        common_elements = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Na', 'Mg', 'Al', 'Si', 'Fe', 'Cu', 'Zn']
        for element in common_elements:
            assert element in constants.ATOMIC_WEIGHTS

    def test_atomic_weight_range(self):
        """Verify atomic weights are positive and reasonable."""
        for weight in constants.ATOMIC_WEIGHTS.values():
            assert weight > 0
            assert weight < 300  # No element heavier than 300 g/mol

    def test_conversion_factors_positive(self):
        """Verify all conversion factors are positive."""
        assert constants.KELVIN_TO_CELSIUS > 0
        assert constants.GPA_TO_PA > 0
        assert constants.MEV_TO_EV > 0
        assert constants.PA_TO_GPA > 0
        assert constants.EV_TO_MEV > 0
        assert constants.CELSIUS_TO_KELVIN > 0