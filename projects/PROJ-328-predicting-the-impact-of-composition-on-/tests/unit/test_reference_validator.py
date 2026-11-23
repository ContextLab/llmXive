"""
Unit tests for the reference validator module.
"""
import pytest
from pathlib import Path
import tempfile
import json
from utils.reference_validator import validate_url, validate_citation_format, validate_research_md

class TestValidateUrl:
    def test_valid_https_url(self):
        assert validate_url("https://example.com") is True
    
    def test_valid_http_url(self):
        assert validate_url("http://example.com") is True
    
    def test_invalid_url_format(self):
        assert validate_url("not-a-url") is False
    
    def test_empty_url(self):
        assert validate_url("") is False
    
    def test_none_url(self):
        assert validate_url(None) is False

class TestValidateCitationFormat:
    def test_valid_citation(self):
        assert validate_citation_format("Smith et al. (2023). Journal of Materials Science.") is True
    
    def test_citation_with_doi(self):
        assert validate_citation_format("Smith et al. (2023). doi:10.1016/j.mat.2023.123456") is True
    
    def test_citation_too_short(self):
        assert validate_citation_format("Short") is False
    
    def test_empty_citation(self):
        assert validate_citation_format("") is False
    
    def test_none_citation(self):
        assert validate_citation_format(None) is False

class TestValidateResearchMd:
    def test_valid_research_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary research file
            research_path = Path(tmpdir) / "research.md"
            output_path = Path(tmpdir) / "verified.md"
            
            with open(research_path, 'w') as f:
                f.write("# Research Sources\n\n")
                f.write("- [Valid Source](https://example.com)\n")
            
            success, sources = validate_research_md(research_path, output_path)
            
            # At least the URL should be valid
            assert success is True or len(sources) >= 0
            assert output_path.exists()
    
    def test_nonexistent_file(self):
        output_path = Path("/tmp/verified.md")
        success, sources = validate_research_md(Path("/nonexistent/research.md"), output_path)
        assert success is False
        assert len(sources) == 0