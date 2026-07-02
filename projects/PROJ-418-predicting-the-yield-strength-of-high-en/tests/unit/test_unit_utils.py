"""
Unit tests for unit normalization utilities.
"""

import numpy as np
import pytest

from code.utils.unit_utils import convert_yield_strength, normalize_to_mpa, SUPPORTED_UNITS


class TestUnitConversion:
    def test_gpa_to_mpa_scalar(self):
        """Test GPa to MPa conversion for scalar."""
        result = convert_yield_strength(1.0, "GPa", "MPa")
        assert result == 1000.0

    def test_ksi_to_mpa_scalar(self):
        """Test ksi to MPa conversion for scalar."""
        result = convert_yield_strength(1.0, "ksi", "MPa")
        assert np.isclose(result, 6.89476)

    def test_psi_to_mpa_scalar(self):
        """Test psi to MPa conversion for scalar."""
        result = convert_yield_strength(1000.0, "psi", "MPa")
        assert np.isclose(result, 6.89476)

    def test_pa_to_mpa_scalar(self):
        """Test Pa to MPa conversion for scalar."""
        result = convert_yield_strength(1e6, "Pa", "MPa")
        assert result == 1.0

    def test_mpa_to_mpa_no_change(self):
        """Test MPa to MPa returns same value."""
        result = convert_yield_strength(500.0, "MPa", "MPa")
        assert result == 500.0

    def test_array_conversion(self):
        """Test array conversion."""
        values = np.array([1.0, 2.0, 3.0])
        result = convert_yield_strength(values, "GPa", "MPa")
        expected = np.array([1000.0, 2000.0, 3000.0])
        assert np.allclose(result, expected)

    def test_normalize_to_mpa_wrapper(self):
        """Test normalize_to_mpa wrapper function."""
        result = normalize_to_mpa(1.5, "GPa")
        assert result == 1500.0

    def test_invalid_source_unit(self):
        """Test error on invalid source unit."""
        with pytest.raises(ValueError):
            convert_yield_strength(100.0, "invalid", "MPa")

    def test_invalid_target_unit(self):
        """Test error on invalid target unit."""
        with pytest.raises(ValueError):
            convert_yield_strength(100.0, "MPa", "invalid")

    def test_case_insensitivity(self):
        """Test unit conversion is case insensitive."""
        result1 = convert_yield_strength(1.0, "gpa", "mpa")
        result2 = convert_yield_strength(1.0, "GPA", "MPA")
        assert result1 == result2

    def test_return_type_scalar(self):
        """Test that scalar input returns scalar output."""
        result = convert_yield_strength(1.0, "GPa", "MPa")
        assert isinstance(result, (int, float))

    def test_return_type_array(self):
        """Test that array input returns array output."""
        result = convert_yield_strength(np.array([1.0]), "GPa", "MPa")
        assert isinstance(result, np.ndarray)
