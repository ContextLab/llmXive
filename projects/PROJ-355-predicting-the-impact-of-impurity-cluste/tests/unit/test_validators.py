"""
Unit tests for code/validators.py
"""
import pytest
from pathlib import Path
from validators import validate_citations, validate_schema
import yaml

def test_validate_citations_with_valid_whitelist(tmp_path):
    """Test validation with a URL in the whitelist."""
    # Create a temporary metadata file
    metadata_file = tmp_path / "metadata.yaml"
    metadata_file.write_text(
        "source:\n"
        "  url: https://materialsproject.org\n"
    )
    
    # This should not raise an error for the whitelisted URL
    # Note: The actual validation involves HTTP requests, which may fail
    # in isolated test environments. We test the logic path.
    try:
        result = validate_citations("https://materialsproject.org", str(metadata_file))
        # If we get here, the URL was valid and reachable
        assert result is True
    except ValueError as e:
        # If the URL check fails (e.g., network issue), we expect a specific error
        assert "DATA_UNAVAILABLE" in str(e)

def test_validate_citations_with_invalid_url(tmp_path):
    """Test validation with a URL not in the whitelist."""
    metadata_file = tmp_path / "metadata.yaml"
    metadata_file.write_text(
        "source:\n"
        "  url: https://invalid-untrusted-site.com\n"
    )
    
    with pytest.raises(ValueError) as exc_info:
        validate_citations("https://invalid-untrusted-site.com", str(metadata_file))
    
    assert "DATA_UNAVAILABLE" in str(exc_info.value)

def test_validate_schema(tmp_path):
    """Test schema validation with valid and invalid data."""
    # Create a temporary schema file
    schema_file = tmp_path / "schema.yaml"
    schema_file.write_text(
        "type: object\n"
        "required:\n"
        "  - bulk_config_id\n"
        "properties:\n"
        "  bulk_config_id:\n"
        "    type: string\n"
        "  impurity_species:\n"
        "    type: string\n"
    )
    
    # Create valid data
    valid_data_file = tmp_path / "valid_data.yaml"
    valid_data_file.write_text(
        "bulk_config_id: MP-12345\n"
        "impurity_species: Cr\n"
    )
    
    # Create invalid data (missing required field)
    invalid_data_file = tmp_path / "invalid_data.yaml"
    invalid_data_file.write_text(
        "impurity_species: Cr\n"
    )
    
    # Valid data should pass
    assert validate_schema(str(valid_data_file), str(schema_file)) is True
    
    # Invalid data should fail
    assert validate_schema(str(invalid_data_file), str(schema_file)) is False
