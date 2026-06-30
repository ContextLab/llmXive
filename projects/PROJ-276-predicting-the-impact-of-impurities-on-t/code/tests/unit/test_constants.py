"""
Unit tests for the constants module.
"""

import pytest
from code.src.utils import constants


class TestAtomicWeights:
    def test_magnesium_weight_exists(self):
        """Verify Mg atomic weight is defined."""
        assert "Mg" in constants.ATOMIC_WEIGHTS
        assert constants.ATOMIC_WEIGHTS["Mg"] > 0
    
    def test_boron_weight_exists(self):
        """Verify B atomic weight is defined."""
        assert "B" in constants.ATOMIC_WEIGHTS
        assert constants.ATOMIC_WEIGHTS["B"] > 0
    
    def test_molecular_weight_calculation(self):
        """Verify MgB2 molecular weight calculation."""
        expected = constants.ATOMIC_WEIGHTS["Mg"] + 2 * constants.ATOMIC_WEIGHTS["B"]
        assert abs(constants.MAGNESIUM_BORIDE_MOLECULAR_WEIGHT - expected) < 1e-6
    
    def test_all_weights_positive(self):
        """Verify all atomic weights are positive."""
        for element, weight in constants.ATOMIC_WEIGHTS.items():
            assert weight > 0, f"Atomic weight for {element} should be positive"

class TestUnitConversions:
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
    
    def test_gpa_to_bar(self):
        """Verify GPa to bar conversion factor."""
        assert constants.GPA_TO_BAR == 10000
    
    def test_bar_to_gpa(self):
        """Verify bar to GPa conversion factor."""
        assert constants.BAR_TO_GPA == 1e-4

class TestVIFThresholds:
    def test_vif_threshold_low(self):
        """Verify low VIF threshold value."""
        assert constants.VIF_THRESHOLD_LOW == 5.0
    
    def test_vif_threshold_high(self):
        """Verify high VIF threshold value."""
        assert constants.VIF_THRESHOLD_HIGH == 10.0
    
    def test_default_vif_threshold(self):
        """Verify default VIF threshold matches low threshold."""
        assert constants.VIF_THRESHOLD == constants.VIF_THRESHOLD_LOW
    
    def test_vif_threshold_positive(self):
        """Verify VIF thresholds are positive."""
        assert constants.VIF_THRESHOLD_LOW > 0
        assert constants.VIF_THRESHOLD_HIGH > 0
        assert constants.VIF_THRESHOLD > 0

class TestDataProcessingConstants:
    def test_min_samples_per_impurity(self):
        """Verify minimum samples per impurity constant."""
        assert constants.MIN_SAMPLES_PER_IMPURITY >= 1
    
    def test_max_missing_value_pct(self):
        """Verify max missing value percentage constant."""
        assert 0 <= constants.MAX_MISSING_VALUE_PCT <= 1
    
    def test_default_random_seed(self):
        """Verify default random seed constant."""
        assert constants.DEFAULT_RANDOM_SEED >= 0

class TestConstantsIntegrity:
    def test_mg_formula(self):
        """Verify MgB2 formula string."""
        assert constants.MAGNESIUM_BORIDE_FORMULA == "MgB2"
    
    def test_mg_weight_consistency(self):
        """Verify Mg weight consistency between dict and constant."""
        assert constants.MAGNESIUM_ATOMIC_WEIGHT == constants.ATOMIC_WEIGHTS["Mg"]
    
    def test_b_weight_consistency(self):
        """Verify B weight consistency between dict and constant."""
        assert constants.BORON_ATOMIC_WEIGHT == constants.ATOMIC_WEIGHTS["B"]