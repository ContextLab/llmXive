import pytest
import tempfile
import os
from pathlib import Path
from utils.reference_validator import validate_citation_format, validate_url, validate_research_md, ConstitutionError

def test_validate_citation_format_valid():
    line = "[T008a] Initial Draft | https://example.com"
    result = validate_citation_format(line)
    assert result is not None
    assert result['id'] == "T008a"
    assert result['title'] == "Initial Draft"
    assert result['url'] == "https://example.com"

def test_validate_citation_format_invalid():
    line = "This is just a random line without a URL"
    result = validate_citation_format(line)
    assert result is None

def test_validate_url_invalid_format():
    assert validate_url("not-a-url") is False
    assert validate_url("ftp://example.com") is False

def test_validate_research_md_creates_output(tmp_path):
    # Create a temporary input file with mixed valid/invalid content
    input_file = tmp_path / "research.md"
    input_file.write_text(
        "# Draft\n"
        "[T1] Valid Title | https://httpbin.org/status/200\n"
        "[T2] Invalid URL | not-a-url\n"
        "[T3] Another Valid | https://httpbin.org/status/200\n"
    )
    
    output_file = tmp_path / "research_verified.md"
    
    # This should succeed because at least one URL is valid
    verified = validate_research_md(input_file, output_file)
    
    assert len(verified) == 2
    assert output_file.exists()
    content = output_file.read_text()
    assert "Valid Title" in content
    assert "Another Valid" in content
    assert "not-a-url" not in content

def test_validate_research_md_raises_on_empty(tmp_path):
    # Create an input file with no valid URLs
    input_file = tmp_path / "research.md"
    input_file.write_text(
        "# Draft\n"
        "[T1] Invalid | bad-url\n"
    )
    
    output_file = tmp_path / "research_verified.md"
    
    with pytest.raises(ConstitutionError):
        validate_research_md(input_file, output_file)
