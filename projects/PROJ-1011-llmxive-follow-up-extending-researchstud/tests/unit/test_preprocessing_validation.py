"""
Unit tests for preprocessing validation logic in code/01_data_acquisition.py.

This module specifically tests that the preprocessing pipeline correctly handles
malformed entries, specifically empty or whitespace-only abstracts, as per T019.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

# Import the functions being tested from the data acquisition module
# We use relative imports assuming the test is run with PYTHONPATH set to the project root
# or via pytest discovery from the tests/ directory.
import sys
import os

# Ensure we can import from code/
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.logging_config import get_logger
from utils.error_handling import DataFetchError

# Import the specific functions from 01_data_acquisition
# We need to import the module itself to access the functions
import importlib.util
spec = importlib.util.spec_from_file_location("data_acquisition", code_path / "01_data_acquisition.py")
data_acquisition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_acquisition)

# Aliases for clarity
is_valid_abstract = data_acquisition.is_valid_abstract
filter_malformed_entries = data_acquisition.filter_malformed_entries
normalize_text = data_acquisition.normalize_text
preprocess_corpus = data_acquisition.preprocess_corpus

logger = get_logger(__name__)


class TestPreprocessingValidation:
    """Tests for T019: Preprocessing validation of empty/malformed abstracts."""

    def test_is_valid_abstract_empty_string(self):
        """Test that empty strings are rejected."""
        assert is_valid_abstract("") is False

    def test_is_valid_abstract_whitespace_only(self):
        """Test that whitespace-only strings are rejected."""
        assert is_valid_abstract("   ") is False
        assert is_valid_abstract("\n\t\r") is False

    def test_is_valid_abstract_none(self):
        """Test that None values are rejected."""
        assert is_valid_abstract(None) is False

    def test_is_valid_abstract_valid_text(self):
        """Test that valid text is accepted."""
        assert is_valid_abstract("This is a valid abstract.") is True
        assert is_valid_abstract("Short.") is True  # Assuming any non-empty text is valid

    def test_filter_malformed_entries_removes_empty(self):
        """Test that filter_malformed_entries removes entries with empty abstracts."""
        test_data = [
            {"id": 1, "abstract": "Valid abstract."},
            {"id": 2, "abstract": ""},
            {"id": 3, "abstract": "   "},
            {"id": 4, "abstract": None},
            {"id": 5, "abstract": "Another valid one."},
            {"id": 6, "abstract": "\n\n"},
        ]
        
        filtered = filter_malformed_entries(test_data)
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 5

    def test_filter_malformed_entries_preserves_valid(self):
        """Test that valid entries are preserved in order."""
        test_data = [
            {"id": 1, "abstract": "First"},
            {"id": 2, "abstract": "Second"},
            {"id": 3, "abstract": "Third"},
        ]
        
        filtered = filter_malformed_entries(test_data)
        
        assert len(filtered) == 3
        assert [item["id"] for item in filtered] == [1, 2, 3]

    def test_filter_malformed_entries_all_invalid(self):
        """Test behavior when all entries are invalid."""
        test_data = [
            {"id": 1, "abstract": ""},
            {"id": 2, "abstract": "   "},
        ]
        
        filtered = filter_malformed_entries(test_data)
        
        assert len(filtered) == 0

    def test_preprocess_corpus_with_malformed_input(self):
        """
        Test that preprocess_corpus handles a file with malformed entries.
        It should filter them out and return a clean list.
        """
        # Create a temporary file with mixed valid/invalid data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            valid_entry = {"id": 1, "abstract": "Valid text here.", "title": "Test"}
            invalid_entry = {"id": 2, "abstract": "", "title": "Bad"}
            whitespace_entry = {"id": 3, "abstract": "   \n", "title": "Bad"}
            
            f.write(json.dumps(valid_entry) + '\n')
            f.write(json.dumps(invalid_entry) + '\n')
            f.write(json.dumps(whitespace_entry) + '\n')
            temp_path = f.name

        try:
            # Run the preprocessing
            result = preprocess_corpus(temp_path)
            
            # Assertions
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == 1
            assert result[0]["abstract"] == "Valid text here."
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_preprocess_corpus_raises_on_file_not_found(self):
        """Test that preprocess_corpus fails loudly if input file is missing."""
        with pytest.raises(FileNotFoundError):
            preprocess_corpus("/nonexistent/path/corpus.jsonl")

    def test_normalize_text_handles_whitespace(self):
        """Test that normalize_text properly cleans up whitespace."""
        raw = "   This   is   a   test.   "
        normalized = normalize_text(raw)
        assert normalized == "This is a test."
        assert "  " not in normalized

    def test_integration_empty_abstract_in_corpus(self):
        """
        Integration test: Simulate the full flow of loading a raw corpus
        with injected malformed entries and verifying they are filtered.
        """
        # Construct a mock raw corpus list similar to what T011 would produce
        raw_corpus = [
            {
                "id": "arxiv_001",
                "title": "Deep Learning for Climate",
                "abstract": "We propose a new method...",
                "venue": "arXiv",
                "acceptance_status": "accepted"
            },
            {
                "id": "arxiv_002",
                "title": "Empty Abstract Study",
                "abstract": "",  # Malformed
                "venue": "arXiv",
                "acceptance_status": "accepted"
            },
            {
                "id": "arxiv_003",
                "title": "Whitespace Abstract",
                "abstract": "   \t  ",  # Malformed
                "venue": "arXiv",
                "acceptance_status": "accepted"
            },
            {
                "id": "arxiv_004",
                "title": "Normal Abstract",
                "abstract": "Another valid entry.",
                "venue": "arXiv",
                "acceptance_status": "accepted"
            }
        ]

        # Use the filter function directly on the list
        cleaned_corpus = filter_malformed_entries(raw_corpus)

        # Verify count
        assert len(cleaned_corpus) == 2

        # Verify specific IDs are present
        ids = [item["id"] for item in cleaned_corpus]
        assert "arxiv_001" in ids
        assert "arxiv_004" in ids
        assert "arxiv_002" not in ids
        assert "arxiv_003" not in ids

        # Verify content integrity
        assert cleaned_corpus[0]["abstract"] == "We propose a new method..."
        assert cleaned_corpus[1]["abstract"] == "Another valid entry."