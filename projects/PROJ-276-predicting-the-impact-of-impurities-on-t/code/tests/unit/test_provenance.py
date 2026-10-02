"""
Unit tests for data provenance generation.
"""
import pytest
from code.src.utils.data_provenance import generate_provenance_header


class TestProvenance:
    def test_generate_provenance_header_keys(self):
        """Verify the function returns a dictionary containing exactly these keys: source, timestamp, version."""
        source = "Materials Project"
        timestamp = "2023-10-27T10:00:00Z"
        version = "1.0.0"

        result = generate_provenance_header(source, timestamp, version)

        assert isinstance(result, dict), "Result must be a dictionary"
        
        # Check for required keys
        assert "source" in result, "Result must contain 'source' key"
        assert "timestamp" in result, "Result must contain 'timestamp' key"
        assert "version" in result, "Result must contain 'version' key"

        # Check for exactly these keys (no extra keys)
        assert set(result.keys()) == {"source", "timestamp", "version"}, \
            "Result must contain exactly the keys: source, timestamp, version"

    def test_generate_provenance_header_values(self):
        """Verify the values in the dictionary match the inputs."""
        source = "SuperCon"
        timestamp = "2024-01-01T12:00:00Z"
        version = "2.1.0"

        result = generate_provenance_header(source, timestamp, version)

        assert result["source"] == source
        assert result["timestamp"] == timestamp
        assert result["version"] == version

    def test_generate_provenance_header_empty_strings(self):
        """Verify the function handles empty strings correctly."""
        result = generate_provenance_header("", "", "")
        
        assert result["source"] == ""
        assert result["timestamp"] == ""
        assert result["version"] == ""