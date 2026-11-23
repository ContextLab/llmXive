"""
Unit tests for data provenance generation.
"""
import pytest
import json
from code.src.utils.data_provenance import generate_provenance_header


class TestProvenance:
    """Tests for the generate_provenance_header function."""

    def test_basic_format(self):
        """Test that the output starts with the correct prefix and is valid JSON."""
        source = "test_source"
        timestamp = "2023-10-27T10:00:00Z"
        version = "1.0.0"

        result = generate_provenance_header(source, timestamp, version)

        assert result.startswith("# PROVENANCE: "), "Output must start with '# PROVENANCE: '"

        json_part = result[len("# PROVENANCE: "):]
        parsed = json.loads(json_part)

        assert parsed["source"] == source
        assert parsed["timestamp"] == timestamp
        assert parsed["version"] == version

    def test_minified_json(self):
        """Test that the JSON part is minified (no extra whitespace)."""
        result = generate_provenance_header("src", "ts", "v1")
        json_part = result[len("# PROVENANCE: "):]

        # Minified JSON should not contain spaces after colons or commas
        assert " " not in json_part, "JSON should be minified (no spaces)"

    def test_additional_metadata(self):
        """Test that additional metadata is included in the output."""
        source = "src"
        timestamp = "ts"
        version = "v1"
        meta = {"user": "alice", "run_id": 123}

        result = generate_provenance_header(source, timestamp, version, additional_metadata=meta)
        json_part = result[len("# PROVENANCE: "):]
        parsed = json.loads(json_part)

        assert parsed["user"] == "alice"
        assert parsed["run_id"] == 123

    def test_utf8_encoding(self):
        """Test that the output is valid UTF-8."""
        result = generate_provenance_header("src", "ts", "v1")
        # Attempt to encode to UTF-8 bytes to verify validity
        result.encode('utf-8')

    def test_special_characters_in_source(self):
        """Test handling of special characters in source string."""
        source = "Data-Source_123"
        timestamp = "2023-01-01T00:00:00Z"
        version = "1.0"

        result = generate_provenance_header(source, timestamp, version)
        json_part = result[len("# PROVENANCE: "):]
        parsed = json.loads(json_part)

        assert parsed["source"] == source