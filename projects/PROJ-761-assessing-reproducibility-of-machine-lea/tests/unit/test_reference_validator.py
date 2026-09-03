"""
Unit tests for the Reference Validator agent.

Tests the core logic of citation extraction, verified dataset parsing,
and validation without requiring network access.
"""
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from reference_validator import (
    extract_urls_and_dois,
    extract_verified_datasets,
    validate_citation
)

class TestExtractUrlsAndDois:
    def test_extract_urls(self):
        text = "Check out https://example.com and http://test.org/path"
        urls = extract_urls_and_dois(text)
        assert "https://example.com" in urls
        assert "http://test.org/path" in urls
        assert len(urls) == 2

    def test_extract_dois(self):
        text = "See DOI: 10.1021/acs.jcim.1c00001 and 10.1038/s41586-021-00000-0"
        dois = extract_urls_and_dois(text)
        assert "10.1021/acs.jcim.1c00001" in dois
        assert "10.1038/s41586-021-00000-0" in dois
        assert len(dois) == 2

    def test_mixed_citations(self):
        text = "URL: https://example.com, DOI: 10.1000/test"
        citations = extract_urls_and_dois(text)
        assert "https://example.com" in citations
        assert "10.1000/test" in citations
        assert len(citations) == 2

class TestExtractVerifiedDatasets:
    def test_extract_simple_block(self):
        text = """
        Some text before.
        VERIFIED REAL DATA SOURCE
        - package: uspto
        - url: https://example.com/uspto
        - doi: 10.1000/test
        Some text after.
        """
        verified = extract_verified_datasets(text)
        assert verified.get('package') == 'uspto'
        assert verified.get('url') == 'https://example.com/uspto'
        assert verified.get('doi') == '10.1000/test'

    def test_extract_list_items(self):
        text = """
        VERIFIED REAL DATA SOURCE
        - packages:
          - uspto
          - reaxys
        """
        verified = extract_verified_datasets(text)
        # The parser handles list items under a key
        assert 'packages' in verified or 'items' in verified

    def test_no_block(self):
        text = "No verified datasets here."
        verified = extract_verified_datasets(text)
        assert verified == {}

class TestValidateCitation:
    def test_valid_doi(self):
        verified = {'dois': ['10.1000/test']}
        is_valid, msg = validate_citation('10.1000/test', verified)
        assert is_valid is True
        assert 'verified' in msg.lower()

    def test_invalid_doi(self):
        verified = {'dois': ['10.1000/other']}
        is_valid, msg = validate_citation('10.1000/test', verified)
        assert is_valid is False
        assert 'not found' in msg.lower()

    def test_valid_url(self):
        verified = {'urls': ['https://example.com']}
        is_valid, msg = validate_citation('https://example.com', verified)
        assert is_valid is True

    def test_invalid_url(self):
        verified = {'urls': ['https://other.com']}
        is_valid, msg = validate_citation('https://example.com', verified)
        assert is_valid is False

    def test_url_with_package_name(self):
        verified = {'packages': ['uspto']}
        is_valid, msg = validate_citation('https://example.com/uspto-data', verified)
        assert is_valid is True
        assert 'package' in msg.lower()

    def test_unrecognized_format(self):
        verified = {}
        is_valid, msg = validate_citation('some-random-string', verified)
        assert is_valid is False
        assert 'unrecognized' in msg.lower()

class TestIntegration:
    def test_full_validation_flow(self):
        """Test a realistic research.md snippet."""
        text = """
        # Research Summary
        
        We used data from https://example.com/uspto and DOI 10.1000/valid-doi.
        
        ## Verified Datasets
        VERIFIED REAL DATA SOURCE
        - packages:
          - uspto
        - urls:
          - https://example.com/uspto
        - dois:
          - 10.1000/valid-doi
        """
        
        verified = extract_verified_datasets(text)
        citations = extract_urls_and_dois(text)
        
        assert len(citations) == 2
        
        for citation in citations:
            is_valid, _ = validate_citation(citation, verified)
            assert is_valid is True, f"Citation {citation} should be valid"
