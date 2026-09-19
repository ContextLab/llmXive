import pytest
from code.src.utils.data_provenance import generate_provenance_header

class TestProvenance:
    def test_generate_provenance_header_returns_dict(self):
        """Verify the function returns a dictionary."""
        result = generate_provenance_header("test_source", "2023-01-01T00:00:00Z", "v1.0.0")
        assert isinstance(result, dict)

    def test_generate_provenance_header_keys(self):
        """Verify the dictionary contains exactly the required keys."""
        result = generate_provenance_header("test_source", "2023-01-01T00:00:00Z", "v1.0.0")
        
        expected_keys = {"source", "timestamp", "version"}
        assert set(result.keys()) == expected_keys

    def test_generate_provenance_header_values(self):
        """Verify the dictionary values match the inputs."""
        source_val = "MaterialsProject"
        time_val = "2024-05-20T12:30:00Z"
        version_val = "0.1.0"
        
        result = generate_provenance_header(source_val, time_val, version_val)
        
        assert result["source"] == source_val
        assert result["timestamp"] == time_val
        assert result["version"] == version_val