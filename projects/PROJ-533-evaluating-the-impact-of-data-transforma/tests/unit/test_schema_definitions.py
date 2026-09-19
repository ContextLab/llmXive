"""
Unit tests for schema definitions.
"""
import pytest
from code.utils.schema_definitions import (
    get_imputation_log_headers,
    get_exclusions_headers,
    get_filter_results_headers
)

def test_imputation_log_headers():
    """Test that imputation log headers are correct."""
    expected = ["dataset_id", "variable", "imputation_method", "rate"]
    assert get_imputation_log_headers() == expected

def test_exclusions_headers():
    """Test that exclusions log headers are correct."""
    expected = ["dataset_id", "reason", "details"]
    assert get_exclusions_headers() == expected

def test_filter_results_headers():
    """Test that filter results headers are correct."""
    expected = ["dataset_id", "shapiro_p", "sample_size", "included"]
    assert get_filter_results_headers() == expected

def test_headers_are_lists_of_strings():
    """Test that all header functions return lists of strings."""
    for func in [get_imputation_log_headers, get_exclusions_headers, get_filter_results_headers]:
        headers = func()
        assert isinstance(headers, list)
        assert all(isinstance(h, str) for h in headers)
        assert len(headers) > 0