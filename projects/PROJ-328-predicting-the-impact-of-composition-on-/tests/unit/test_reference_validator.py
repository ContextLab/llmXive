"""
Unit tests for the Reference Validator module.
"""
import pytest
import tempfile
import os
from pathlib import Path
from code.utils.reference_validator import (
    validate_url,
    validate_citation_format,
    validate_research_md,
    ConstitutionError
)

class TestValidateUrl:
    """Tests for URL validation."""
    
    def test_valid_http_url(self):
        """Test validation of a valid HTTP URL."""
        url = "http://example.com/path?query=value"
        is_valid, error = validate_url(url)
        assert is_valid is True
        assert error is None
    
    def test_valid_https_url(self):
        """Test validation of a valid HTTPS URL."""
        url = "https://example.com/path"
        is_valid, error = validate_url(url)
        assert is_valid is True
        assert error is None
    
    def test_invalid_url_no_protocol(self):
        """Test validation of a URL without protocol."""
        url = "example.com/path"
        is_valid, error = validate_url(url)
        assert is_valid is False
        assert "Invalid URL format" in error
    
    def test_invalid_url_javascript(self):
        """Test validation of a javascript: URL."""
        url = "javascript:alert('xss')"
        is_valid, error = validate_url(url)
        assert is_valid is False
        assert "Blocked protocol" in error
    
    def test_empty_url(self):
        """Test validation of an empty URL."""
        url = ""
        is_valid, error = validate_url(url)
        assert is_valid is False
        assert "URL is empty" in error
    
    def test_none_url(self):
        """Test validation of None URL."""
        url = None
        is_valid, error = validate_url(url)
        assert is_valid is False
        assert "URL is empty" in error

class TestValidateCitationFormat:
    """Tests for citation format validation."""
    
    def test_valid_citation(self):
        """Test validation of a valid citation format."""
        line = "[1] Materials Project Database - https://materialsproject.org"
        is_valid, error = validate_citation_format(line)
        assert is_valid is True
        assert error is None
    
    def test_invalid_citation_no_url(self):
        """Test validation of a citation without URL."""
        line = "[1] Materials Project Database"
        is_valid, error = validate_citation_format(line)
        assert is_valid is False
        assert "missing URL" in error
    
    def test_invalid_citation_no_title(self):
        """Test validation of a citation without title."""
        line = "https://materialsproject.org"
        is_valid, error = validate_citation_format(line)
        assert is_valid is False
        assert "missing title" in error
    
    def test_empty_citation(self):
        """Test validation of an empty citation."""
        line = ""
        is_valid, error = validate_citation_format(line)
        assert is_valid is False
        assert "Empty citation" in error

class TestValidateResearchMd:
    """Tests for the main validation function."""
    
    def test_valid_file(self):
        """Test validation with a file containing valid entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "candidate_sources.txt"
            output_path = Path(tmpdir) / "research_verified.md"
            
            # Write valid entries
            with open(input_path, 'w') as f:
                f.write("# Test file\n")
                f.write("[1] Materials Project - https://materialsproject.org\n")
                f.write("[2] NIST Database - https://nist.gov/materials\n")
            
            # Validate
            result = validate_research_md(str(input_path), str(output_path))
            
            assert result is True
            assert output_path.exists()
            
            # Check output content
            with open(output_path, 'r') as f:
                content = f.read()
                assert "Materials Project" in content
                assert "NIST Database" in content
    
    def test_invalid_file(self):
        """Test validation with a file containing only invalid entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "candidate_sources.txt"
            output_path = Path(tmpdir) / "research_verified.md"
            
            # Write invalid entries
            with open(input_path, 'w') as f:
                f.write("# Test file\n")
                f.write("[1] Invalid - no_url\n")
                f.write("[2] Invalid - javascript:alert('xss')\n")
            
            # Validation should fail
            with pytest.raises(ConstitutionError):
                validate_research_md(str(input_path), str(output_path))
    
    def test_missing_input_file(self):
        """Test validation with a non-existent input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.txt"
            output_path = Path(tmpdir) / "research_verified.md"
            
            with pytest.raises(ConstitutionError):
                validate_research_md(str(input_path), str(output_path))
    
    def test_mixed_valid_invalid(self):
        """Test validation with a mix of valid and invalid entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "candidate_sources.txt"
            output_path = Path(tmpdir) / "research_verified.md"
            
            # Write mixed entries
            with open(input_path, 'w') as f:
                f.write("# Test file\n")
                f.write("[1] Valid - https://example.com\n")
                f.write("[2] Invalid - no_url\n")
                f.write("[3] Valid - https://example.org\n")
                f.write("[4] Invalid - javascript:alert('xss')\n")
            
            # Validate
            result = validate_research_md(str(input_path), str(output_path))
            
            assert result is True
            assert output_path.exists()
            
            # Check output content
            with open(output_path, 'r') as f:
                content = f.read()
                assert "Valid - https://example.com" in content
                assert "Valid - https://example.org" in content
                assert "Invalid" not in content