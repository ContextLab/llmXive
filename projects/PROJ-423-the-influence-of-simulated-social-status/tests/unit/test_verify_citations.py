import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from verify_citations import parse_sources_file, validate_doi, MIN_TITLE_OVERLAP

def test_parse_sources_file_valid():
    """Test parsing a valid markdown sources file."""
    test_content = """
    # Sources List
    - doi: 10.1038/nature12345
      title: "Example Title One"
    - doi: 10.1126/science.1234567
      title: "Example Title Two"
    """
    with open("test_sources.md", "w") as f:
        f.write(test_content)

    try:
        citations = parse_sources_file("test_sources.md")
        assert len(citations) == 2
        assert citations[0]['doi'] == "10.1038/nature12345"
        assert citations[0]['title'] == "Example Title One"
        assert citations[1]['doi'] == "10.1126/science.1234567"
    finally:
        if os.path.exists("test_sources.md"):
            os.remove("test_sources.md")

def test_parse_sources_file_empty():
    """Test parsing an empty file."""
    with open("test_empty.md", "w") as f:
        f.write("")
    
    try:
        citations = parse_sources_file("test_empty.md")
        assert len(citations) == 0
    finally:
        if os.path.exists("test_empty.md"):
            os.remove("test_empty.md")

@patch('verify_citations.CrossrefRestAPI')
def test_validate_doi_success(mock_api_class):
    """Test successful DOI validation with high overlap."""
    mock_api_instance = MagicMock()
    mock_api_class.return_value = mock_api_instance
    
    # Mock metadata response
    mock_api_instance.works.return_value = {
        "message": {
            "title": ["Example Title One"]
        }
    }

    result = validate_doi("10.1038/nature12345", "Example Title One")
    
    assert result['valid'] is True
    assert result['doi'] == "10.1038/nature12345"
    assert result['metadata_title'] == "Example Title One"
    assert result['overlap_score'] == 1.0

@patch('verify_citations.CrossrefRestAPI')
def test_validate_doi_low_overlap(mock_api_class):
    """Test DOI validation with low title overlap."""
    mock_api_instance = MagicMock()
    mock_api_class.return_value = mock_api_instance
    
    # Mock metadata response with different title
    mock_api_instance.works.return_value = {
        "message": {
            "title": ["Completely Different Title"]
        }
    }

    result = validate_doi("10.1038/nature12345", "Example Title One")
    
    assert result['valid'] is False
    assert "overlap" in result['reason'].lower()

@patch('verify_citations.CrossrefRestAPI')
def test_validate_doi_not_found(mock_api_class):
    """Test DOI validation when DOI is not found."""
    mock_api_instance = MagicMock()
    mock_api_class.return_value = mock_api_instance
    
    # Mock empty response
    mock_api_instance.works.return_value = None

    result = validate_doi("10.1038/nonexistent", "Some Title")
    
    assert result['valid'] is False
    assert "not found" in result['reason'].lower()