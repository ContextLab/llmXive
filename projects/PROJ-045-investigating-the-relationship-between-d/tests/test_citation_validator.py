"""
Tests for the citation verification module (T001).

These tests verify the logic of the citation validator without requiring
network access for every run (using mocks for the API calls).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path if necessary
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.citation_validator import (
    verify_citation,
    run_verification,
    save_report,
    CRITICAL_CITATIONS
)

class TestCitationValidator:
    """Test cases for citation verification logic."""

    def test_verify_citation_success(self, caplog):
        """Test successful verification of a known citation."""
        citation = {
            "id": "test_success",
            "author": "Albert Einstein",
            "title": "On the Electrodynamics of Moving Bodies",
            "year": 1905,
            "type": "article",
            "reason": "Foundational physics paper."
        }
        
        # Mock the fetch function to return a matching result
        mock_metadata = {
            "title": ["On the Electrodynamics of Moving Bodies"],
            "author": [{"family": "Einstein", "given": "Albert"}],
            "DOI": "10.1002/andp.19053221004",
            "type": "journal-article"
        }

        with patch('code.citation_validator.fetch_crossref_metadata', return_value=mock_metadata):
            result = verify_citation(citation, caplog)
            
            assert result['verified'] is True
            assert result['source_found'] is not None
            assert result['critical_failure'] is False

    def test_verify_citation_failure(self, caplog):
        """Test verification failure when no match is found."""
        citation = {
            "id": "test_fail",
            "author": "Unknown Author",
            "title": "A Fake Paper Title That Does Not Exist",
            "year": 2099,
            "type": "article",
            "reason": "Test failure case."
        }
        
        with patch('code.citation_validator.fetch_crossref_metadata', return_value=None):
            result = verify_citation(citation, caplog)
            
            assert result['verified'] is False
            assert result['source_found'] is None
            assert "Could not verify" in result['details']

    def test_verify_citation_critical_failure(self, caplog):
        """Test that critical citations are flagged correctly on failure."""
        citation = {
            "id": "test_critical",
            "author": "Linus Pauling",
            "title": "The Nature of the Chemical Bond",
            "year": 1960,
            "type": "book",
            "reason": "Cited by reviewer Linus Pauling."
        }
        
        with patch('code.citation_validator.fetch_crossref_metadata', return_value=None):
            result = verify_citation(citation, caplog)
            
            assert result['verified'] is False
            assert result['critical_failure'] is True

    def test_save_report_creates_file(self, tmp_path):
        """Test that save_report writes a valid JSON file."""
        report = {
            "timestamp": "2026-01-01",
            "total_citations": 1,
            "verified_count": 1,
            "failed_count": 0,
            "critical_failures": False,
            "citations": []
        }
        
        output_file = tmp_path / "test_report.json"
        
        # Patch the global OUTPUT_PATH to use our temp file
        with patch('code.citation_validator.OUTPUT_PATH', output_file):
            # We need to mock setup_logging to avoid file creation issues in test env
            with patch('code.citation_validator.setup_logging'):
                save_report(report, MagicMock())
                
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
            assert data['total_citations'] == 1

    def test_run_verification_structure(self, caplog):
        """Test the structure of the full verification report."""
        # Mock the individual verification to return a fixed result
        mock_result = {
            "id": "mocked",
            "verified": True,
            "source_found": "Mock Source",
            "details": "Mocked",
            "critical_failure": False
        }
        
        with patch('code.citation_validator.verify_citation', return_value=mock_result):
            # We need to mock the CRITICAL_CITATIONS list to be small and predictable
            test_citations = [{
                "id": "mocked",
                "author": "Test",
                "title": "Test",
                "year": 2000,
                "type": "article",
                "reason": "Test"
            }]
            
            with patch('code.citation_validator.CRITICAL_CITATIONS', test_citations):
                with patch('code.citation_validator.setup_logging'):
                    report = run_verification(MagicMock())
                    
                    assert 'timestamp' in report
                    assert 'citations' in report
                    assert 'critical_failures' in report
                    assert report['total_citations'] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
