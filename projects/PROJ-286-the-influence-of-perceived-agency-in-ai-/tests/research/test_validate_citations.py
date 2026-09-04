"""
Unit tests for the citation validation logic in code/research/validate_citations.py.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.research.validate_citations import (
    tokenize,
    calculate_similarity,
    fetch_crossref_data,
    validate_citation,
    parse_documents,
    write_citation_log
)


class TestTokenize:
    def test_tokenize_simple(self):
        text = "Hello World"
        tokens = tokenize(text)
        assert "hello" in tokens
        assert "world" in tokens
        assert len(tokens) == 2

    def test_tokenize_empty(self):
        assert tokenize("") == []
        assert tokenize(None) == []


class TestCalculateSimilarity:
    def test_identical_strings(self):
        assert calculate_similarity("hello", "hello") == 1.0

    def test_different_strings(self):
        score = calculate_similarity("hello", "world")
        assert score < 1.0
        assert score >= 0.0

    def test_empty_strings(self):
        assert calculate_similarity("", "") == 0.0
        assert calculate_similarity("hello", "") == 0.0


class TestValidateCitation:
    @patch('code.research.validate_citations.fetch_crossref_data')
    def test_valid_citation(self, mock_fetch):
        mock_fetch.return_value = {
            "title": ["Trust in Automation: Integrating Empirical Evidence on Factors That Influence Trust"]
        }
        result = validate_citation(
            doi="10.1234/test",
            claimed_title="Trust in Automation: Integrating Empirical Evidence on Factors That Influence Trust",
            citation_key="Test"
        )
        assert result["status"] == "verified"
        assert result["content_verified"] is True

    @patch('code.research.validate_citations.fetch_crossref_data')
    def test_invalid_overlap(self, mock_fetch):
        mock_fetch.return_value = {
            "title": ["Completely Different Title"]
        }
        result = validate_citation(
            doi="10.1234/test",
            claimed_title="Trust in Automation",
            citation_key="Test"
        )
        assert result["status"] == "failed"
        assert result["content_verified"] is False

    @patch('code.research.validate_citations.fetch_crossref_data')
    def test_fetch_failure(self, mock_fetch):
        mock_fetch.return_value = None
        result = validate_citation(
            doi="10.1234/test",
            claimed_title="Some Title",
            citation_key="Test"
        )
        assert result["status"] == "failed"
        assert "Failed to fetch" in result.get("error", "")


class TestMainExecution:
    def test_parse_documents_returns_list(self):
        citations = parse_documents()
        assert isinstance(citations, list)
        assert len(citations) > 0
        # Check if the hardcoded Lee & See citation is present
        found = False
        for c in citations:
            if c["key"] == "Lee & See (2004)":
                found = True
                assert c["doi"] == "10.1518/hfes.46.1.50_30392"
        assert found, "Lee & See (2004) citation not found in parsed documents"

    def test_write_citation_log_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_report.json"
            data = [{"key": "test", "status": "ok"}]
            write_citation_log(data, output_path)
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded == data