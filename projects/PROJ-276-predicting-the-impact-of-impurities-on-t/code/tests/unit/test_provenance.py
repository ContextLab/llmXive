"""
Unit tests for data provenance utilities.
"""
import pytest
from code.src.utils.data_provenance import generate_provenance_header


class TestProvenance:
    """Test suite for generate_provenance_header function."""

    def test_generate_provenance_header_returns_dict(self):
        """Verify the function returns a dictionary."""
        result = generate_provenance_header("test_source", "2023-01-01T00:00:00", "1.0.0")
        assert isinstance(result, dict)

    def test_generate_provenance_header_contains_required_keys(self):
        """Verify the function returns a dictionary containing exactly these keys: source, timestamp, version."""
        result = generate_provenance_header("Materials Project", "2023-10-27T10:00:00", "v1.0.0")

        expected_keys = {"source", "timestamp", "version"}
        assert set(result.keys()) == expected_keys, f"Expected keys {expected_keys}, got {set(result.keys())}"

    def test_generate_provenance_header_values_match_input(self):
        """Verify the dictionary values match the input arguments."""
        source = "SuperCon"
        timestamp = "2024-05-15T14:30:00"
        version = "2.1.0-beta"

        result = generate_provenance_header(source, timestamp, version)

        assert result["source"] == source
        assert result["timestamp"] == timestamp
        assert result["version"] == version

    def test_generate_provenance_header_with_empty_strings(self):
        """Verify the function handles empty string inputs correctly."""
        result = generate_provenance_header("", "", "")
        assert result["source"] == ""
        assert result["timestamp"] == ""
        assert result["version"] == ""

    def test_generate_provenance_header_key_count_is_exactly_three(self):
        """Verify the dictionary contains exactly three keys."""
        result = generate_provenance_header("source", "timestamp", "version")
        assert len(result) == 3