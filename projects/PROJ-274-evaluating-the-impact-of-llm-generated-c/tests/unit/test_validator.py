import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.validator import (
    tokenize_title, 
    calculate_jaccard_similarity, 
    validate_reference,
    validate_document_references
)

class TestTokenization:
    def test_tokenize_simple(self):
        tokens = tokenize_title("Hello World")
        assert "hello" in tokens
        assert "world" in tokens
        assert len(tokens) == 2

    def test_tokenize_case_insensitive(self):
        tokens1 = tokenize_title("Hello")
        tokens2 = tokenize_title("HELLO")
        assert tokens1 == tokens2

    def test_tokenize_special_chars(self):
        tokens = tokenize_title("Hello, World! 123")
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens

class TestJaccardSimilarity:
    def test_identical(self):
        tokens = ["a", "b", "c"]
        assert calculate_jaccard_similarity(tokens, tokens) == 1.0

    def test_no_overlap(self):
        tokens1 = ["a", "b"]
        tokens2 = ["c", "d"]
        assert calculate_jaccard_similarity(tokens1, tokens2) == 0.0

    def test_partial_overlap(self):
        tokens1 = ["a", "b", "c"]
        tokens2 = ["a", "d"]
        # Intersection: {a} (1)
        # Union: {a, b, c, d} (4)
        assert calculate_jaccard_similarity(tokens1, tokens2) == 0.25

    def test_empty(self):
        assert calculate_jaccard_similarity([], []) == 0.0
        assert calculate_jaccard_similarity(["a"], []) == 0.0

class TestValidateReference:
    @patch('utils.validator.fetch_citation_metadata')
    def test_valid_reference(self, mock_fetch):
        mock_fetch.return_value = {
            "title": "Real Paper Title",
            "author": [],
            "DOI": "10.1234/test"
        }
        citation = {
            "id": "1",
            "url": "10.1234/test",
            "title": "Real Paper Title"
        }
        result = validate_reference(citation)
        assert result["valid"] is True
        assert result["similarity"] == 1.0
        assert result["reason"].startswith("Similarity: 1.00")

    @patch('utils.validator.fetch_citation_metadata')
    def test_low_similarity(self, mock_fetch):
        mock_fetch.return_value = {
            "title": "Completely Different Title",
            "author": [],
            "DOI": "10.1234/test"
        }
        citation = {
            "id": "1",
            "url": "10.1234/test",
            "title": "Real Paper Title"
        }
        result = validate_reference(citation)
        assert result["valid"] is False
        assert result["similarity"] < 0.7

    @patch('utils.validator.fetch_citation_metadata')
    def test_fetch_failure(self, mock_fetch):
        mock_fetch.return_value = None
        citation = {
            "id": "1",
            "url": "10.1234/test",
            "title": "Real Paper Title"
        }
        result = validate_reference(citation)
        assert result["valid"] is False
        assert "Could not fetch" in result["reason"]

    def test_missing_url(self):
        citation = {
            "id": "1",
            "url": "",
            "title": "Real Paper Title"
        }
        result = validate_reference(citation)
        assert result["valid"] is False
        assert "Missing URL" in result["reason"]

class TestValidateDocumentReferences:
    def test_validate_document_references_integration(self, tmp_path):
        # Create a mock citations.yaml
        citations_data = [
            {"id": "1", "url": "10.1234/test", "title": "Test Title"},
            {"id": "2", "url": "10.5678/other", "title": "Other Title"}
        ]
        citations_path = tmp_path / "citations.yaml"
        import yaml
        with open(citations_path, 'w') as f:
            yaml.dump(citations_data, f)

        # Mock the fetch function to return specific data
        with patch('utils.validator.fetch_citation_metadata') as mock_fetch:
            # Mock first as valid, second as invalid
            mock_fetch.side_effect = [
                {"title": "Test Title", "DOI": "10.1234/test"},
                {"title": "Wrong Title", "DOI": "10.5678/other"}
            ]
            
            result = validate_document_references(citations_path)
            
            assert result["status"] == "some_invalid"
            assert result["total_citations"] == 2
            assert result["valid_count"] == 1
            assert result["invalid_count"] == 1
            assert len(result["details"]) == 2
            assert result["details"][0]["valid"] is True
            assert result["details"][1]["valid"] is False