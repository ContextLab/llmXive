"""
Unit tests for validation and error handling of effect sizes.
"""
import pytest
import math
from code.utils.validator import validate_effect_size, validate_study_row, filter_valid_studies


class TestValidateEffectSize:
    def test_valid_positive_correlation(self):
        is_valid, err = validate_effect_size(0.5, 100, "S1", 1)
        assert is_valid is True
        assert err is None

    def test_valid_negative_correlation(self):
        is_valid, err = validate_effect_size(-0.5, 100, "S1", 1)
        assert is_valid is True
        assert err is None

    def test_valid_zero_correlation(self):
        is_valid, err = validate_effect_size(0.0, 100, "S1", 1)
        assert is_valid is True
        assert err is None

    def test_missing_r(self):
        is_valid, err = validate_effect_size(None, 100, "S1", 1)
        assert is_valid is False
        assert "Missing effect size data" in err

    def test_missing_n(self):
        is_valid, err = validate_effect_size(0.5, None, "S1", 1)
        assert is_valid is False
        assert "Missing effect size data" in err

    def test_invalid_n_zero(self):
        is_valid, err = validate_effect_size(0.5, 0, "S1", 1)
        assert is_valid is False
        assert "Invalid sample size" in err

    def test_invalid_n_negative(self):
        is_valid, err = validate_effect_size(0.5, -5, "S1", 1)
        assert is_valid is False
        assert "Invalid sample size" in err

    def test_r_out_of_range_high(self):
        is_valid, err = validate_effect_size(1.5, 100, "S1", 1)
        assert is_valid is False
        assert "out of range" in err

    def test_r_out_of_range_low(self):
        is_valid, err = validate_effect_size(-1.5, 100, "S1", 1)
        assert is_valid is False
        assert "out of range" in err

    def test_nan_r(self):
        is_valid, err = validate_effect_size(float('nan'), 100, "S1", 1)
        assert is_valid is False
        assert "NaN" in err

    def test_inf_r(self):
        is_valid, err = validate_effect_size(float('inf'), 100, "S1", 1)
        assert is_valid is False
        assert "Inf" in err


class TestFilterValidStudies:
    def test_filter_mixed_studies(self):
        studies = [
            {"study_id": "S1", "r": 0.5, "n": 100, "row_index": 1},
            {"study_id": "S2", "r": None, "n": 100, "row_index": 2}, # Invalid
            {"study_id": "S3", "r": 0.2, "n": 50, "row_index": 3},
            {"study_id": "S4", "r": 1.5, "n": 100, "row_index": 4}, # Invalid
        ]

        valid, excluded = filter_valid_studies(studies)

        assert len(valid) == 2
        assert len(excluded) == 2

        assert valid[0]["study_id"] == "S1"
        assert valid[1]["study_id"] == "S3"

        excluded_ids = [x["study"]["study_id"] for x in excluded]
        assert "S2" in excluded_ids
        assert "S4" in excluded_ids

    def test_all_invalid(self):
        studies = [
            {"study_id": "S1", "r": None, "n": 100, "row_index": 1},
        ]
        valid, excluded = filter_valid_studies(studies)
        assert len(valid) == 0
        assert len(excluded) == 1