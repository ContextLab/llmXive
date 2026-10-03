"""
Unit tests for schema definitions and validation logic.
Tests the headers and row validation for imputation_log, exclusions, and filter_results.
"""
import pytest
from code.utils.schema_definitions import (
    get_imputation_log_headers,
    get_exclusions_headers,
    get_filter_results_headers,
    validate_imputation_log_row,
    validate_exclusions_row,
    validate_filter_results_row,
    IMPUTATION_LOG_HEADERS,
    EXCLUSIONS_HEADERS,
    FILTER_RESULTS_HEADERS
)

class TestSchemaHeaders:
    def test_imputation_log_headers(self):
        """Verify imputation_log.csv headers match specification."""
        expected = ["dataset_id", "variable", "imputation_method", "rate"]
        assert get_imputation_log_headers() == expected

    def test_exclusions_headers(self):
        """Verify exclusions.csv headers match specification."""
        expected = ["dataset_id", "reason", "details"]
        assert get_exclusions_headers() == expected

    def test_filter_results_headers(self):
        """Verify filter_results.csv headers match specification."""
        expected = ["dataset_id", "shapiro_p", "sample_size", "included"]
        assert get_filter_results_headers() == expected

class TestImputationLogValidation:
    def test_valid_imputation_row(self):
        """Test a valid imputation log row."""
        row = {
            "dataset_id": "ds_001",
            "variable": "age",
            "imputation_method": "median",
            "rate": 0.05
        }
        is_valid, msg = validate_imputation_log_row(row)
        assert is_valid is True
        assert msg == "Valid"

    def test_missing_key_imputation(self):
        """Test validation fails on missing key."""
        row = {
            "dataset_id": "ds_001",
            "variable": "age",
            # missing imputation_method and rate
        }
        is_valid, msg = validate_imputation_log_row(row)
        assert is_valid is False
        assert "Missing required keys" in msg

    def test_invalid_rate_type(self):
        """Test validation fails on non-numeric rate."""
        row = {
            "dataset_id": "ds_001",
            "variable": "age",
            "imputation_method": "mean",
            "rate": "not_a_number"
        }
        is_valid, msg = validate_imputation_log_row(row)
        assert is_valid is False
        assert "rate must be a numeric value" in msg

class TestExclusionsValidation:
    def test_valid_exclusion_row(self):
        """Test a valid exclusions row."""
        row = {
            "dataset_id": "ds_002",
            "reason": "missing_rate",
            "details": "missing_rate: 15.5"
        }
        is_valid, msg = validate_exclusions_row(row)
        assert is_valid is True
        assert msg == "Valid"

    def test_missing_key_exclusions(self):
        """Test validation fails on missing key."""
        row = {
            "dataset_id": "ds_002",
            # missing reason and details
        }
        is_valid, msg = validate_exclusions_row(row)
        assert is_valid is False
        assert "Missing required keys" in msg

class TestFilterResultsValidation:
    def test_valid_filter_row(self):
        """Test a valid filter results row."""
        row = {
            "dataset_id": "ds_003",
            "shapiro_p": 0.03,
            "sample_size": 150,
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is True
        assert msg == "Valid"

    def test_valid_filter_row_string_bool(self):
        """Test validation accepts string boolean for included."""
        row = {
            "dataset_id": "ds_003",
            "shapiro_p": 0.03,
            "sample_size": 150,
            "included": "False"
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is True
        assert msg == "Valid"

    def test_invalid_shapiro_p_type(self):
        """Test validation fails on non-numeric shapiro_p."""
        row = {
            "dataset_id": "ds_003",
            "shapiro_p": "invalid",
            "sample_size": 150,
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "shapiro_p must be a numeric value" in msg

    def test_invalid_sample_size_type(self):
        """Test validation fails on non-integer sample_size."""
        row = {
            "dataset_id": "ds_003",
            "shapiro_p": 0.03,
            "sample_size": "invalid",
            "included": True
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "sample_size must be an integer" in msg

    def test_invalid_included_type(self):
        """Test validation fails on invalid included type."""
        row = {
            "dataset_id": "ds_003",
            "shapiro_p": 0.03,
            "sample_size": 150,
            "included": "maybe"
        }
        is_valid, msg = validate_filter_results_row(row)
        assert is_valid is False
        assert "included must be a boolean" in msg