"""
Unit tests for code/validators.py
"""
import pytest
from pathlib import Path
from validators import validate_citations

def test_validate_citations_empty_metadata(tmp_path):
    """Test validation with an empty metadata file."""
    metadata_file = tmp_path / "metadata.yaml"
    metadata_file.write_text("")
    result = validate_citations("https://materialsproject.org", str(metadata_file))
    assert "success" in result
    assert "error_code" in result

def test_validate_citations_invalid_url(tmp_path):
    """Test validation with an invalid URL."""
    metadata_file = tmp_path / "metadata.yaml"
    metadata_file.write_text("url: invalid-url")
    result = validate_citations("invalid-url", str(metadata_file))
    assert result["success"] is False
    assert result["error_code"] == "URL_INVALID"
