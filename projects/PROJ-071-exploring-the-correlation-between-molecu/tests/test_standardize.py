"""
Unit tests for the standardize module.
Focus: Unit conversion logic (k to half-life) and Arrhenius normalization.
"""
import math
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from standardize import convert_k_to_half_life, normalize_arrhenius

class TestKToHalfLifeConversion:
    """
    T018: Unit test for unit conversion logic.
    Function: test_k_to_half_life_conversion.
    Assertion: t1_2 = ln(2)/0.01 equals 69.31 hours within 0.01.
    """

    def test_k_to_half_life_conversion(self):
        """Verify the conversion from rate constant (k) to half-life (t1/2)."""
        # Given: k = 0.01 (units assumed to be 1/hours for this test context)
        k_value = 0.01
        
        # When: Calculating half-life
        # Formula: t1/2 = ln(2) / k
        calculated_half_life = convert_k_to_half_life(k_value)
        
        # Expected: ln(2) / 0.01
        expected_half_life = math.log(2) / 0.01
        
        # Assert: The calculated value matches the expected value within 0.01
        # Expected value is approx 69.314718...
        assert abs(calculated_half_life - expected_half_life) < 0.01, \
            f"Expected {expected_half_life} but got {calculated_half_life}"
        
        # Specifically check against the task requirement of ~69.31
        assert abs(calculated_half_life - 69.31) < 0.01, \
            f"Result {calculated_half_life} does not match expected 69.31 within tolerance"

    def test_zero_k_raises_error(self):
        """Verify that a zero rate constant raises a ValueError."""
        with pytest.raises(ValueError):
            convert_k_to_half_life(0.0)

    def test_negative_k_raises_error(self):
        """Verify that a negative rate constant raises a ValueError."""
        with pytest.raises(ValueError):
            convert_k_to_half_life(-0.01)

    def test_pandas_series_conversion(self):
        """Verify conversion works on a pandas Series."""
        k_series = pd.Series([0.01, 0.02, 0.03])
        result = convert_k_to_half_life(k_series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        # Check first value
        expected_first = math.log(2) / 0.01
        assert abs(result.iloc[0] - expected_first) < 1e-4

class TestArrheniusNormalization:
    """
    Tests for Arrhenius normalization logic (T020b).
    """

    def test_arrhenius_normalization(self):
        """Verify Arrhenius normalization calculation."""
        # Given:
        # t1/2_meas = 100 hours
        # T_meas = 310 K (37°C)
        # T_std = 298.15 K (25°C)
        # Ea = 50000 J/mol
        # R = 8.314 J/(mol*K)
        
        t_half_meas = 100.0
        t_meas = 310.0
        t_std = 298.15
        ea = 50000.0
        r = 8.314
        
        # When: Normalizing
        t_half_std = normalize_arrhenius(t_half_meas, t_meas, t_std, ea, r)
        
        # Expected: t1/2_std = t1/2_meas * exp(Ea/R * (1/T_meas - 1/T_std))
        expected_factor = math.exp((ea / r) * ((1.0 / t_meas) - (1.0 / t_std)))
        expected_t_half_std = t_half_meas * expected_factor
        
        # Assert
        assert abs(t_half_std - expected_t_half_std) < 1e-4

    def test_missing_ea_returns_none(self):
        """Verify that missing Ea returns None or a flag."""
        # If Ea is None, the function should handle it gracefully
        # The implementation might return None or raise a specific error
        # Based on standardize.py logic, it likely returns None or a specific flag
        result = normalize_arrhenius(100.0, 310.0, 298.15, None, 8.314)
        assert result is None

    def test_identical_temperatures(self):
        """Verify that if T_meas == T_std, t1/2 remains unchanged."""
        t_half = 100.0
        t = 298.15
        ea = 50000.0
        r = 8.314
        
        result = normalize_arrhenius(t_half, t, t, ea, r)
        assert abs(result - t_half) < 1e-6