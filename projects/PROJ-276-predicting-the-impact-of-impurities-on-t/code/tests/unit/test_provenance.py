"""
Unit tests for data provenance utilities.
"""
import pytest
from code.src.utils.data_provenance import generate_provenance_header


class TestProvenance:
    """Tests for the generate_provenance_header function."""

    def test_returns_dict(self):
        """Verify the function returns a dictionary."""
        result = generate_provenance_header("test_source", "2023-01-01T00:00:00Z", "v1.0")
        assert isinstance(result, dict)

    def test_contains_required_keys(self):
        """Verify the dictionary contains exactly the required keys."""
        result = generate_provenance_header("test_source", "2023-01-01T00:00:00Z", "v1.0")
        required_keys = {"source", "timestamp", "version"}
        assert set(result.keys()) == required_keys

    def test_values_match_inputs(self):
        """Verify the dictionary values match the input arguments."""
        src = "Materials Project"
        ts = "2024-05-20T12:30:00Z"
        ver = "1.2.3"
        
        result = generate_provenance_header(src, ts, ver)
        
        assert result["source"] == src
        assert result["timestamp"] == ts
        assert result["version"] == ver

    def test_empty_string_inputs(self):
        """Verify behavior with empty string inputs."""
        result = generate_provenance_header("", "", "")
        assert result["source"] == ""
        assert result["timestamp"] == ""
        assert result["version"] == ""