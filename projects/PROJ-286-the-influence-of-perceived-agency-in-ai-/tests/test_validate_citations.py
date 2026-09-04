import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path if needed, though imports should handle relative structure
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from research.validate_citations import (
    tokenize,
    calculate_similarity,
    fetch_crossref_data,
    validate_citation,
    write_citation_log
)

class TestTokenize:
    def test_tokenize_normal(self):
        text = "Hello World"
        result = tokenize(text)
        assert result == ["hello", "world"]

    def test_tokenize_empty(self):
        assert tokenize("") == []
        assert tokenize(None) == []

    def test_tokenize_special_chars(self):
        text = "Hello, World!"
        result = tokenize(text)
        assert "hello" in result
        assert "world" in result

class TestCalculateSimilarity:
    def test_identical(self):
        assert calculate_similarity("test", "test") == 1.0

    def test_different(self):
        score = calculate_similarity("test", "best")
        assert score < 1.0
        assert score > 0.0

    def test_empty(self):
        assert calculate_similarity("", "") == 0.0
        assert calculate_similarity("test", "") == 0.0

class TestFetchCrossrefData:
    @patch('research.validate_citations.requests.get')
    def test_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "message": {
                "title": ["Trust in Automation"],
                "author": [{"family": "Lee"}]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        data = fetch_crossref_data("10.1234/test")
        assert data is not None
        assert data["title"] == ["Trust in Automation"]

    @patch('research.validate_citations.requests.get')
    def test_failure_404(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = mock_response

        data = fetch_crossref_data("10.1234/nonexistent")
        assert data is None

class TestValidateCitation:
    def test_valid_citation(self):
        citation = {
            "author": "Lee & See",
            "year": 2004,
            "claimed_title": "Trust in Automation: Designing for Appropriate Reliance",
            "doi": "10.1518/hfes.46.1.50_30392"
        }
        
        # Mock the fetch function to return expected metadata
        with patch('research.validate_citations.fetch_crossref_data') as mock_fetch:
            mock_fetch.return_value = {
                "title": ["Trust in Automation: Designing for Appropriate Reliance"],
                "author": [{"family": "Lee"}, {"family": "See"}]
            }
            
            result = validate_citation(citation)
            assert result["status"] == "verified"
            assert result["content_verified"] is True
            assert result["overlap_score"] > 0.7

    def test_invalid_title(self):
        citation = {
            "author": "Lee & See",
            "year": 2004,
            "claimed_title": "Completely Wrong Title",
            "doi": "10.1518/hfes.46.1.50_30392"
        }
        
        with patch('research.validate_citations.fetch_crossref_data') as mock_fetch:
            mock_fetch.return_value = {
                "title": ["Trust in Automation: Designing for Appropriate Reliance"]
            }
            
            result = validate_citation(citation)
            assert result["status"] == "failed"
            assert result["content_verified"] is False

    def test_missing_doi(self):
        citation = {
            "author": "Unknown",
            "year": 2020,
            "claimed_title": "Test",
            "doi": None
        }
        
        result = validate_citation(citation)
        assert result["status"] == "failed"
        assert "No DOI provided" in result["error"]

class TestWriteCitationLog:
    def test_write_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            results = [{"status": "verified"}]
            
            write_citation_log(results, str(output_path))
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data == results
