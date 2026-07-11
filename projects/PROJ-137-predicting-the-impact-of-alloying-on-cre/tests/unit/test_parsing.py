"""Unit tests for composition string parsing and normalization.

Tests the composition parsing logic in src/data/preprocess.py to ensure:
1. Composition strings are correctly parsed into element-fraction dictionaries.
2. Strings are normalized (alphabetical sort, consistent formatting).
3. Weight percent to atomic percent conversion works correctly.
4. Edge cases (missing values, malformed strings) are handled gracefully.
"""

import pytest
import numpy as np
from src.data.preprocess import parse_composition, normalize_composition_str, wtp_to_atp


class TestParseComposition:
    """Tests for parse_composition function."""

    def test_simple_binary_alloy(self):
        """Parse a simple binary alloy string."""
        comp_str = "Fe:0.5,Cr:0.5"
        result = parse_composition(comp_str)
        expected = {"Cr": 0.5, "Fe": 0.5}
        assert result == expected

    def test_complex_multicomponent(self):
        """Parse a multicomponent alloy string."""
        comp_str = "Ni:0.6,Cr:0.2,Fe:0.1,Co:0.1"
        result = parse_composition(comp_str)
        expected = {"Co": 0.1, "Cr": 0.2, "Fe": 0.1, "Ni": 0.6}
        assert result == expected

    def test_handles_whitespace(self):
        """Parse composition string with irregular whitespace."""
        comp_str = " Fe : 0.5 , Cr : 0.5 "
        result = parse_composition(comp_str)
        expected = {"Cr": 0.5, "Fe": 0.5}
        assert result == expected

    def test_handles_missing_values(self):
        """Parse composition string with missing values (None)."""
        comp_str = "Fe:0.5,Cr:None,Al:0.5"
        result = parse_composition(comp_str)
        expected = {"Al": 0.5, "Fe": 0.5}
        assert result == expected

    def test_invalid_format_raises_error(self):
        """Raise ValueError for invalid composition format."""
        with pytest.raises(ValueError):
            parse_composition("Fe0.5,Cr0.5")  # Missing colon

    def test_non_numeric_fraction_raises_error(self):
        """Raise ValueError for non-numeric fraction."""
        with pytest.raises(ValueError):
            parse_composition("Fe:abc,Cr:0.5")

    def test_empty_string_raises_error(self):
        """Raise ValueError for empty string."""
        with pytest.raises(ValueError):
            parse_composition("")

    def test_negative_fraction_raises_error(self):
        """Raise ValueError for negative fraction."""
        with pytest.raises(ValueError):
            parse_composition("Fe:-0.5,Cr:1.5")

    def test_sum_exceeds_one_raises_error(self):
        """Raise ValueError if fractions sum to more than 1."""
        with pytest.raises(ValueError):
            parse_composition("Fe:0.6,Cr:0.6")

    def test_sum_less_than_one_valid(self):
        """Allow sum less than 1 (implicit balance element)."""
        comp_str = "Fe:0.5,Cr:0.4"
        result = parse_composition(comp_str)
        assert result == {"Cr": 0.4, "Fe": 0.5}


class TestNormalizeCompositionStr:
    """Tests for normalize_composition_str function."""

    def test_sorts_alphabetically(self):
        """Normalize sorts elements alphabetically."""
        input_str = "Fe:0.5,Cr:0.5"
        result = normalize_composition_str(input_str)
        expected = "Cr:0.5,Fe:0.5"
        assert result == expected

    def test_rounds_fractions(self):
        """Normalize rounds fractions to 4 decimal places."""
        input_str = "Fe:0.33333333,Cr:0.66666667"
        result = normalize_composition_str(input_str)
        expected = "Cr:0.6667,Fe:0.3333"
        assert result == expected

    def test_removes_trailing_zeros(self):
        """Normalize removes unnecessary trailing zeros."""
        input_str = "Fe:0.5000,Cr:0.5000"
        result = normalize_composition_str(input_str)
        expected = "Cr:0.5,Fe:0.5"
        assert result == expected

    def test_handles_missing_values(self):
        """Normalize removes None values."""
        input_str = "Fe:0.5,Cr:None,Al:0.5"
        result = normalize_composition_str(input_str)
        expected = "Al:0.5,Fe:0.5"
        assert result == expected


class TestWtpToAtp:
    """Tests for wtp_to_atp function."""

    def test_binary_alloy_conversion(self):
        """Convert weight percent to atomic percent for binary alloy."""
        # 50 wt% Fe, 50 wt% Cr
        # Atomic weights: Fe=55.845, Cr=51.996
        wtp = {"Fe": 0.5, "Cr": 0.5}
        result = wtp_to_atp(wtp)

        # Manual calculation:
        # moles_Fe = 0.5 / 55.845 = 0.008953
        # moles_Cr = 0.5 / 51.996 = 0.009616
        # total_moles = 0.018569
        # atp_Fe = 0.008953 / 0.018569 = 0.4822
        # atp_Cr = 0.009616 / 0.018569 = 0.5178
        expected = {"Cr": pytest.approx(0.5178, rel=0.01), "Fe": pytest.approx(0.4822, rel=0.01)}
        assert result["Fe"] == expected["Fe"]
        assert result["Cr"] == expected["Cr"]

    def test_multicomponent_conversion(self):
        """Convert weight percent to atomic percent for multicomponent alloy."""
        wtp = {"Ni": 0.6, "Cr": 0.2, "Fe": 0.1, "Co": 0.1}
        result = wtp_to_atp(wtp)

        # Verify sum is approximately 1.0
        assert np.isclose(sum(result.values()), 1.0, rtol=1e-4)

        # Verify all values are positive
        assert all(v > 0 for v in result.values())

    def test_single_element(self):
        """Convert single element (should return 1.0)."""
        wtp = {"Fe": 1.0}
        result = wtp_to_atp(wtp)
        expected = {"Fe": 1.0}
        assert result == expected

    def test_invalid_element_raises_error(self):
        """Raise KeyError for unknown element."""
        wtp = {"Fe": 0.5, "UnknownElement": 0.5}
        with pytest.raises(KeyError):
            wtp_to_atp(wtp)

    def test_empty_dict_raises_error(self):
        """Raise ValueError for empty dictionary."""
        with pytest.raises(ValueError):
            wtp_to_atp({})

    def test_sum_not_one_raises_error(self):
        """Raise ValueError if sum is not approximately 1."""
        wtp = {"Fe": 0.6, "Cr": 0.6}
        with pytest.raises(ValueError):
            wtp_to_atp(wtp)

    def test_negative_weight_raises_error(self):
        """Raise ValueError for negative weight percent."""
        wtp = {"Fe": -0.5, "Cr": 1.5}
        with pytest.raises(ValueError):
            wtp_to_atp(wtp)