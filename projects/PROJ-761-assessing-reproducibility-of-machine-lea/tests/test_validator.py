"""
Unit tests for code/validator.py
"""
import os
import tempfile
import logging
from pathlib import Path
import pytest

# Import the functions to test
# Note: We need to ensure the code directory is in the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validator import (
    extract_verified_datasets,
    extract_citations,
    validate_citation,
    run_validation,
    setup_logging
)

class TestExtractVerifiedDatasets:
    def test_basic_parsing(self):
        content = """
        ### Verified Datasets
        - US-1 Dataset: https://example.com/us1
        - US-2 Dataset: 10.1234/us2
        """
        result = extract_verified_datasets(content)
        assert "us-1 dataset" in result
        assert result["us-1 dataset"] == "https://example.com/us1"
        assert "us-2 dataset" in result
        assert result["us-2 dataset"] == "10.1234/us2"

    def test_no_section(self):
        content = "No verified datasets here."
        result = extract_verified_datasets(content)
        assert result == {}

    def test_malformed_lines(self):
        content = """
        ### Verified Datasets
        - No colon here
        - Valid: https://example.com
        - Another: 10.1234/doi
        """
        result = extract_verified_datasets(content)
        assert len(result) == 2
        assert "valid" in result

class TestExtractCitations:
    def test_doi_extraction(self):
        content = "See paper 10.1038/s41586-023-06000-0 for details."
        citations = extract_citations(content)
        dois = [c['value'] for c in citations if c['type'] == 'doi']
        assert len(dois) == 1
        assert dois[0] == "10.1038/s41586-023-06000-0"

    def test_url_extraction(self):
        content = "Data available at https://example.com/data."
        citations = extract_citations(content)
        urls = [c['value'] for c in citations if c['type'] == 'url']
        assert len(urls) == 1
        assert urls[0] == "https://example.com/data"

    def test_mixed_extraction(self):
        content = "DOI 10.1234/abc and URL https://example.com."
        citations = extract_citations(content)
        assert len(citations) == 2

class TestValidateCitation:
    def test_doi_match(self):
        verified = {"dataset": "10.1234/abc"}
        citation = {"type": "doi", "value": "10.1234/abc"}
        is_valid, msg = validate_citation(citation, verified)
        assert is_valid
        assert "matches" in msg

    def test_url_match(self):
        verified = {"dataset": "https://example.com"}
        citation = {"type": "url", "value": "https://example.com"}
        is_valid, msg = validate_citation(citation, verified)
        assert is_valid

    def test_no_match(self):
        verified = {"dataset": "10.1234/abc"}
        citation = {"type": "doi", "value": "10.9999/xyz"}
        is_valid, msg = validate_citation(citation, verified)
        assert not is_valid
        assert "not found" in msg

class TestRunValidation:
    def test_success_case(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            content = """
            ### Verified Datasets
            - Test Data: 10.1234/test
            
            We used the test data 10.1234/test in our study.
            """
            research_path.write_text(content)
            success = run_validation(research_path)
            assert success

    def test_failure_case(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            content = """
            ### Verified Datasets
            - Test Data: 10.1234/test
            
            We used an unknown DOI 10.9999/unknown.
            """
            research_path.write_text(content)
            success = run_validation(research_path)
            assert not success

    def test_missing_verified_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            content = "No verified datasets block here."
            research_path.write_text(content)
            success = run_validation(research_path)
            assert not success