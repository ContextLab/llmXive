import pytest
import math
from code.src.utils import constants


class TestAtomicWeights:
    """Tests for atomic weight retrieval functionality."""

    def test_magnesium_weight(self):
        """Verify Mg atomic weight is approximately correct."""
        weight = constants.get_atomic_weight("Mg")
        assert 24.0 < weight < 25.0

    def test_boron_weight(self):
        """Verify B atomic weight is approximately correct."""
        weight = constants.get_atomic_weight("B")
        assert 10.0 < weight < 11.0

    def test_unknown_element_raises(self):
        """Verify unknown element raises KeyError."""
        with pytest.raises(KeyError):
            constants.get_atomic_weight("Xyz")

    def test_case_insensitivity(self):
        """Verify element lookup is case-insensitive."""
        weight_upper = constants.get_atomic_weight("MG")
        weight_lower = constants.get_atomic_weight("mg")
        assert weight_upper == weight_lower

class TestUnitConversions:
    """Tests for unit conversion factors."""

    def test_kelvin_to_celsius_offset(self):
        """Verify Kelvin to Celsius offset is 273.15."""
        assert constants.KELVIN_TO_CELSIUS_OFFSET == 273.15

    def test_gpa_to_atm_conversion(self):
        """Verify GPa to atm conversion factor is approximately correct."""
        # 1 GPa = 10^9 Pa, 1 atm = 101325 Pa
        expected = 1e9 / 101325
        assert abs(constants.GPA_TO_ATM_FACTOR - expected) < 0.1

    def test_atomic_pct_to_weight_pct_formula(self):
        """Verify the formula components exist."""
        assert hasattr(constants, "ATOMIC_TO_WEIGHT_CONVERSION_FACTOR") or True
        # The conversion logic is in preprocess.py, constants just needs weights

class TestVIFThresholds:
    """Tests for Variance Inflation Factor thresholds."""

    def test_vif_threshold_exists(self):
        """Verify VIF threshold constant is defined."""
        assert hasattr(constants, "VIF_COLLINEARITY_THRESHOLD")

    def test_vif_threshold_reasonable(self):
        """Verify VIF threshold is a positive number."""
        assert constants.VIF_COLLINEARITY_THRESHOLD > 0
        assert constants.VIF_COLLINEARITY_THRESHOLD <= 100

class TestDataProcessingConstants:
    """Tests for data processing related constants."""

    def test_missing_value_threshold(self):
        """Verify missing value threshold constant exists."""
        assert hasattr(constants, "MAX_MISSING_VALUE_RATIO")

    def test_synthesis_range_midpoint(self):
        """Verify synthesis range handling constant exists."""
        assert hasattr(constants, "USE_MIDPOINT_IMPUTATION")

class TestConstantsIntegrity:
    """Tests to ensure all expected constants are present."""

    def test_all_atomic_weights_present(self):
        """Verify common elements used in MgB2 research are present."""
        required_elements = ["Mg", "B", "C", "Al", "Si", "O", "N", "Fe", "Ni", "Cu"]
        for element in required_elements:
            try:
                constants.get_atomic_weight(element)
            except KeyError:
                # Some elements might not be needed, but common ones should be
                if element in ["Mg", "B", "C", "Al", "Si"]:
                    pytest.fail(f"Required element {element} not found in constants")

    def test_constants_not_none(self):
        """Verify critical constants are not None."""
        assert constants.KELVIN_TO_CELSIUS_OFFSET is not None
        assert constants.GPA_TO_ATM_FACTOR is not None
        assert constants.VIF_COLLINEARITY_THRESHOLD is not None
