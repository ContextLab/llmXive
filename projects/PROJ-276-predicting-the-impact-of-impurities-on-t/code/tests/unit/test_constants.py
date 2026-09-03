"""
Unit tests for the constants module.
"""
import pytest
from code.src.utils import constants


class TestAtomicWeights:
    """Tests for the ATOMIC_WEIGHTS dictionary and get_atomic_weight function."""

    def test_magnesium_weight(self):
        """Verify Mg atomic weight."""
        assert constants.ATOMIC_WEIGHTS["Mg"] == 24.3050

    def test_boron_weight(self):
        """Verify B atomic weight."""
        assert constants.ATOMIC_WEIGHTS["B"] == 10.8100

    def test_get_atomic_weight_valid(self):
        """Test retrieving a valid atomic weight."""
        assert constants.get_atomic_weight("Fe") == 55.8450

    def test_get_atomic_weight_invalid(self):
        """Test that invalid element raises KeyError."""
        with pytest.raises(KeyError):
            constants.get_atomic_weight("Xy")


class TestUnitConversions:
    """Tests for unit conversion factors."""

    def test_gpa_to_pascal(self):
        """Verify GPa to Pascal conversion."""
        assert constants.GPA_TO_PASCAL == 1e9

    def test_gpa_to_bar(self):
        """Verify GPa to Bar conversion."""
        assert constants.GPA_TO_BAR == 10000.0

    def test_kelvin_to_celsius_offset(self):
        """Verify Kelvin to Celsius offset."""
        assert constants.KELVIN_TO_CELSIUS_OFFSET == 273.15


class TestVIFThresholds:
    """Tests for VIF threshold constants."""

    def test_conservative_threshold(self):
        """Verify conservative VIF threshold is 5.0."""
        assert constants.VIF_THRESHOLD_CONSERVATIVE == 5.0

    def test_strict_threshold(self):
        """Verify strict VIF threshold is 10.0."""
        assert constants.VIF_THRESHOLD_STRICT == 10.0


class TestDataProcessingConstants:
    """Tests for data processing constants."""

    def test_min_feature_samples(self):
        """Verify minimum feature samples."""
        assert constants.MIN_FEATURE_SAMPLES == 10

    def test_common_impurities(self):
        """Verify common impurities list contains expected elements."""
        assert "C" in constants.COMMON_IMPURITY_ELEMENTS
        assert "Si" in constants.COMMON_IMPURITY_ELEMENTS
        assert "Al" in constants.COMMON_IMPURITY_ELEMENTS


class TestConstantsIntegrity:
    """Tests to ensure constants module integrity."""

    def test_all_weights_positive(self):
        """Verify all atomic weights are positive."""
        for weight in constants.ATOMIC_WEIGHTS.values():
            assert weight > 0

    def test_conversion_factors_positive(self):
        """Verify conversion factors are positive."""
        assert constants.GPA_TO_PASCAL > 0
        assert constants.GPA_TO_BAR > 0
        assert constants.GPA_TO_MPA > 0