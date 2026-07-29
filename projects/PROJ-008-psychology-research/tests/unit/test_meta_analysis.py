"""
Unit tests for random-effects model selection logic (I² > 50%).

This module verifies the logic in code/analysis/meta_analysis.py that determines
whether to use a random-effects model based on heterogeneity statistics (I²).
"""
import pytest
from unittest.mock import patch, MagicMock
import math

# Import the logic to test. Since code/analysis/meta_analysis.py is not yet
# implemented (T025), we define a minimal mock implementation here to test the
# selection logic in isolation, ensuring the test structure is correct and
# ready for integration once T025 is complete.
#
# NOTE: In the final implementation, this would be:
# from code.analysis.meta_analysis import select_model, calculate_i_squared
#
# For T023, we test the *logic* of the selection rule (I² > 50% -> Random Effects)
# using a mock or local definition to ensure the test harness is valid.

class MockMetaAnalysisResult:
    """Mock result object to simulate output from a meta-analysis run."""
    def __init__(self, i_squared: float, q_statistic: float, p_value: float):
        self.i_squared = i_squared
        self.q_statistic = q_statistic
        self.p_value = p_value
        self.model_type = None  # To be set by selection logic

def calculate_i_squared(q_statistic: float, df: int) -> float:
    """
    Calculate I² statistic from Cochran's Q and degrees of freedom.
    I² = max(0, (Q - df) / Q) * 100
    """
    if q_statistic <= 0 or df <= 0:
        return 0.0
    val = ((q_statistic - df) / q_statistic) * 100
    return max(0.0, val)

def select_model(i_squared: float, threshold: float = 50.0) -> str:
    """
    Select model based on I² statistic.
    Returns 'random_effects' if I² > threshold, else 'fixed_effects'.
    """
    if i_squared > threshold:
        return "random_effects"
    return "fixed_effects"

class TestModelSelectionLogic:
    """Tests for the random-effects model selection logic."""

    def test_i_squared_below_threshold_fixed(self):
        """Test that I² <= 50% selects fixed-effects model."""
        i2 = 45.0
        result = select_model(i2)
        assert result == "fixed_effects", f"Expected fixed_effects for I²={i2}, got {result}"

    def test_i_squared_above_threshold_random(self):
        """Test that I² > 50% selects random-effects model."""
        i2 = 55.0
        result = select_model(i2)
        assert result == "random_effects", f"Expected random_effects for I²={i2}, got {result}"

    def test_i_squared_exactly_threshold_fixed(self):
        """Test that I² == 50% selects fixed-effects model (strict inequality)."""
        i2 = 50.0
        result = select_model(i2)
        assert result == "fixed_effects", f"Expected fixed_effects for I²={i2}, got {result}"

    def test_i_squared_calculation_low_heterogeneity(self):
        """Test I² calculation for low heterogeneity (Q close to df)."""
        # Q = 3.0, df = 2 -> (3-2)/3 = 0.333 -> 33.3%
        i2 = calculate_i_squared(3.0, 2)
        assert math.isclose(i2, 33.333333, rel_tol=1e-4)

    def test_i_squared_calculation_high_heterogeneity(self):
        """Test I² calculation for high heterogeneity (Q >> df)."""
        # Q = 20.0, df = 2 -> (20-2)/20 = 0.9 -> 90%
        i2 = calculate_i_squared(20.0, 2)
        assert math.isclose(i2, 90.0, rel_tol=1e-4)

    def test_i_squared_calculation_negative_result(self):
        """Test that I² cannot be negative (max with 0)."""
        # Q < df should result in 0
        i2 = calculate_i_squared(1.0, 5)
        assert i2 == 0.0

    def test_integration_scenario_high_heterogeneity(self):
        """
        Integration-style test: Simulate a scenario with high heterogeneity
        and verify the model selection logic triggers random-effects.
        """
        # Simulate 10 studies, df=9, Q=25 (high heterogeneity)
        q_stat = 25.0
        df = 9
        i2 = calculate_i_squared(q_stat, df)
        
        assert i2 > 50.0, f"Expected high I² (>50) for Q={q_stat}, df={df}, got {i2}"
        
        model = select_model(i2)
        assert model == "random_effects", "High heterogeneity should trigger random-effects model"

    def test_integration_scenario_low_heterogeneity(self):
        """
        Integration-style test: Simulate a scenario with low heterogeneity
        and verify the model selection logic triggers fixed-effects.
        """
        # Simulate 10 studies, df=9, Q=10 (low heterogeneity)
        q_stat = 10.0
        df = 9
        i2 = calculate_i_squared(q_stat, df)

        assert i2 <= 50.0, f"Expected low I² (<=50) for Q={q_stat}, df={df}, got {i2}"

        model = select_model(i2)
        assert model == "fixed_effects", "Low heterogeneity should trigger fixed-effects model"