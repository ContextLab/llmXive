"""
Tests for the citation validation utility.
"""
import pytest
import os
import tempfile
from pathlib import Path
from code.utils.validate_citations import (
    parse_research_md,
    is_verified_source,
    validate_citations,
    VERIFIED_DATASETS
)

class TestCitationParsing:
    def test_parse_research_md_with_citations(self, tmp_path):
        """Test parsing of research.md with standard citations."""
        content = """
        # Research
        
        We analyzed Planck data [1].
        See https://pla.esa.int for details.
        Also check arxiv.org/abs/1234.5678 for methodology.
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)
        
        citations = parse_research_md(file_path)
        
        assert len(citations) == 2
        urls = [c[0] for c in citations]
        assert "https://pla.esa.int" in urls
        assert "https://arxiv.org/abs/1234.5678" in urls

    def test_parse_research_md_empty(self, tmp_path):
        """Test parsing of empty file."""
        file_path = tmp_path / "research.md"
        file_path.write_text("# No citations here")
        
        citations = parse_research_md(file_path)
        assert len(citations) == 0

    def test_parse_research_md_missing_file(self, tmp_path):
        """Test parsing of non-existent file."""
        file_path = tmp_path / "nonexistent.md"
        
        citations = parse_research_md(file_path)
        assert len(citations) == 0

class TestVerifiedSource:
    def test_planck_url(self):
        """Test Planck Legacy Archive URL."""
        assert is_verified_source("https://pla.esa.int/planck")
        assert is_verified_source("http://archives.esac.esa.int/pla/data")

    def test_arxiv_url(self):
        """Test arXiv URL."""
        assert is_verified_source("https://arxiv.org/abs/2001.00000")
        assert is_verified_source("https://arxiv.org/pdf/2001.00000.pdf")

    def test_camb_url(self):
        """Test CAMB URL."""
        assert is_verified_source("https://camb.info")

    def test_invalid_url(self):
        """Test invalid/unknown URL."""
        assert not is_verified_source("https://fake-data-source.com")
        assert not is_verified_source("https://example.com/random")

class TestValidationIntegration:
    def test_validate_citations_full_flow(self, tmp_path):
        """Test the full validation flow."""
        # Create a mock research.md
        content = """
        # Research
        
        Valid Planck link: https://pla.esa.int
        Valid ArXiv link: https://arxiv.org/abs/1111.1111
        Invalid link: https://this-does-not-exist-12345.com
        """
        research_file = tmp_path / "research.md"
        research_file.write_text(content)
        
        output_file = tmp_path / "report.json"
        
        results = validate_citations(research_file, output_file)
        
        assert results["total"] == 3
        # The invalid URL might be unreachable, but we check logic
        # The planck and arxiv are verified sources
        assert len(results["missing_verified"]) == 1 # The fake one
        
        # Check that report was written
        assert output_file.exists()

    def test_validate_citations_no_output_path(self, tmp_path):
        """Test validation without writing output file."""
        content = "Link: https://arxiv.org/abs/1111.1111"
        research_file = tmp_path / "research.md"
        research_file.write_text(content)
        
        results = validate_citations(research_file)
        
        assert results["total"] == 1
        assert len(results["missing_verified"]) == 0