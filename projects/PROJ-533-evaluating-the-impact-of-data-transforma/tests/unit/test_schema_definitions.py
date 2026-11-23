import pytest
from code.utils.schema_definitions import (
    get_filter_results_headers,
    validate_filter_results_row,
    get_imputation_log_headers,
    get_exclusions_headers,
    validate_imputation_log_row,
    validate_exclusions_row
)

class TestFilterResultsSchema:
    def test_get_filter_results_headers(self):
        headers = get_filter_results_headers()
        assert headers == ["dataset_id", "shapiro_p", "sample_size", "included"]

    def test_valid_filter_results_row(self):
        row = {
            "dataset_id": "uci_iris",
            "shapiro_p": 0.03,
            "sample_size": 150,
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is True
        assert msg == ""

    def test_valid_filter_results_row_string_bool(self):
        row = {
            "dataset_id": "openml_123",
            "shapiro_p": 0.8,
            "sample_size": 50,
            "included": "false"
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is True
        assert msg == ""
        assert row["included"] is False

    def test_invalid_dataset_id_missing(self):
        row = {
            "shapiro_p": 0.05,
            "sample_size": 30,
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "Missing required columns" in msg

    def test_invalid_shapiro_p_type(self):
        row = {
            "dataset_id": "test",
            "shapiro_p": "not_a_float",
            "sample_size": 30,
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "shapiro_p must be a valid float" in msg

    def test_invalid_shapiro_p_range(self):
        row = {
            "dataset_id": "test",
            "shapiro_p": 1.5,
            "sample_size": 30,
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "shapiro_p must be between 0.0 and 1.0" in msg

    def test_invalid_sample_size_negative(self):
        row = {
            "dataset_id": "test",
            "shapiro_p": 0.5,
            "sample_size": -10,
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "sample_size must be non-negative" in msg

    def test_invalid_included_type(self):
        row = {
            "dataset_id": "test",
            "shapiro_p": 0.5,
            "sample_size": 30,
            "included": 123
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "included must be a boolean" in msg

class TestImputationLogSchema:
    def test_get_imputation_log_headers(self):
        headers = get_imputation_log_headers()
        assert headers == ["dataset_id", "variable", "imputation_method", "rate"]

    def test_valid_imputation_log_row(self):
        row = {
            "dataset_id": "test_ds",
            "variable": "age",
            "imputation_method": "median",
            "rate": 5.5
        }
        is_valid, msg = validate_imputation_log_row(row)
        assert is_valid is True
        assert msg == ""

    def test_invalid_rate_range(self):
        row = {
            "dataset_id": "test_ds",
            "variable": "age",
            "imputation_method": "mean",
            "rate": 150.0
        }
        is_valid, msg = validate_imputation_log_row(row)
        assert is_valid is False
        assert "rate must be between 0.0 and 100.0" in msg

class TestExclusionsSchema:
    def test_get_exclusions_headers(self):
        headers = get_exclusions_headers()
        assert headers == ["dataset_id", "reason", "details"]

    def test_valid_exclusions_row(self):
        row = {
            "dataset_id": "test_ds",
            "reason": "missing_rate",
            "details": "missing_rate: 12.5"
        }
        is_valid, msg = validate_exclusions_row(row)
        assert is_valid is True
        assert msg == ""

    def test_valid_exclusions_row_empty_details(self):
        row = {
            "dataset_id": "test_ds",
            "reason": "small_sample",
            "details": ""
        }
        is_valid, msg = validate_exclusions_row(row)
        assert is_valid is True
        assert msg == ""