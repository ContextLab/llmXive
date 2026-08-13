"""
Unit tests for the Reference Validator Agent (T008).

These tests verify the logic of the Constitution Check without requiring
the actual file system state (except for mocking).
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from utils.reference_validator import (
    check_research_md_exists,
    extract_citations,
    verify_citations,
    validate_research_md,
    ConstitutionError,
    RESEARCH_MD_PATH
)

# Sample content for testing
VALID_CONTENT = """
# Research Sources

We utilize data from the **Materials Project** (https://materialsproject.org)
and **NIST** databases.
OpenAlloy provides additional composition data.
The Literature Corpus includes PDFs from various journals.

References:
- DOI: 10.1038/s41524-020-00430-1
- URL: https://www.nist.gov/publications
"""

INVALID_CONTENT_NO_SOURCES = """
# Research

This is a placeholder document with no real sources or citations.
"""

INVALID_CONTENT_NO_URLS = """
# Research

We use data from Materials Project and NIST.
But we forgot to add any URLs or DOIs.
"""

def test_extract_citations_valid():
    """Test that valid citations are extracted correctly."""
    citations = extract_citations(VALID_CONTENT)
    url_citations = [c for c in citations if c[0] == "URL"]
    doi_citations = [c for c in citations if c[0] == "DOI"]

    assert len(url_citations) >= 2
    assert len(doi_citations) >= 1
    assert any("materialsproject.org" in c[1] for c in url_citations)
    assert any("10.1038" in c[1] for c in doi_citations)

def test_extract_citations_empty():
    """Test that empty content yields no citations."""
    citations = extract_citations(INVALID_CONTENT_NO_SOURCES)
    assert len(citations) == 0

def test_verify_citations_valid():
    """Test verification passes for valid content."""
    is_valid, missing = verify_citations(VALID_CONTENT)
    assert is_valid is True
    assert len(missing) == 0

def test_verify_citations_missing_sources():
    """Test verification fails when sources are missing."""
    is_valid, missing = verify_citations(INVALID_CONTENT_NO_SOURCES)
    assert is_valid is False
    assert len(missing) > 0

def test_verify_citations_missing_urls():
    """Test verification fails when no URLs/DOIs are present."""
    is_valid, missing = verify_citations(INVALID_CONTENT_NO_URLS)
    assert is_valid is False
    assert len(missing) == 0  # Sources might be found by keyword, but no URLs

@patch("pathlib.Path.exists", return_value=False)
def test_validate_research_md_missing_file(mock_exists):
    """Test that validate_research_md raises ConstitutionError if file is missing."""
    with pytest.raises(ConstitutionError) as excinfo:
        validate_research_md()
    assert "does not exist" in str(excinfo.value)

@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.read_text", return_value=INVALID_CONTENT_NO_SOURCES)
def test_validate_research_md_invalid_content(mock_read, mock_exists):
    """Test that validate_research_md raises ConstitutionError if content is invalid."""
    with pytest.raises(ConstitutionError) as excinfo:
        validate_research_md()
    assert "Constitution Check FAILED" in str(excinfo.value)

@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.read_text", return_value=VALID_CONTENT)
def test_validate_research_md_success(mock_read, mock_exists):
    """Test that validate_research_md returns True for valid content."""
    result = validate_research_md()
    assert result is True
