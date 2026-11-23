import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import filter_short_abstracts, MIN_ABSTRACT_LENGTH
from utils import save_json, load_json

class TestFilterShortAbstracts:
    def test_filter_removes_short_abstracts(self):
        """Test that abstracts shorter than MIN_ABSTRACT_LENGTH are removed."""
        # Create a mock corpus
        mock_corpus = {
            "author_001": [
                {"text": "a", "id": 1},           # 1 char -> excluded
                {"text": "hello world", "id": 2}, # 11 chars -> kept
                {"text": "ab", "id": 3},          # 2 chars -> excluded
                {"text": "valid text here", "id": 4} # 15 chars -> kept
            ],
            "author_002": [
                {"text": "x", "id": 5},           # 1 char -> excluded
                {"text": "good", "id": 6}         # 4 chars -> excluded (since MIN is 6)
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_corpus.json"
            save_json(mock_corpus, input_path)
            
            output_path, original_count, filtered_count = filter_short_abstracts(input_path)
            
            # Verify counts
            assert original_count == 6
            assert filtered_count == 2  # "hello world" and "valid text here"
            
            # Verify content
            result = load_json(output_path)
            assert len(result["author_001"]) == 2
            assert len(result["author_002"]) == 0
            
            # Verify specific texts remain
            texts_author_1 = [e["text"] for e in result["author_001"]]
            assert "hello world" in texts_author_1
            assert "valid text here" in texts_author_1
            
            # Verify excluded texts are gone
            assert "a" not in texts_author_1
            assert "ab" not in texts_author_1

    def test_filter_boundary_condition(self):
        """Test the exact boundary of MIN_ABSTRACT_LENGTH (6)."""
        mock_corpus = {
            "author_boundary": [
                {"text": "12345", "id": 1},       # 5 chars -> excluded
                {"text": "123456", "id": 2},      # 6 chars -> kept
                {"text": "1234567", "id": 3}      # 7 chars -> kept
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "boundary_corpus.json"
            save_json(mock_corpus, input_path)
            
            _, _, filtered_count = filter_short_abstracts(input_path)
            
            assert filtered_count == 2

    def test_empty_corpus(self):
        """Test handling of an empty corpus."""
        mock_corpus = {}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "empty_corpus.json"
            save_json(mock_corpus, input_path)
            
            output_path, original, filtered = filter_short_abstracts(input_path)
            
            assert original == 0
            assert filtered == 0
            
            result = load_json(output_path)
            assert result == {}

    def test_all_excluded(self):
        """Test when all abstracts are too short."""
        mock_corpus = {
            "author_short": [
                {"text": "a", "id": 1},
                {"text": "b", "id": 2}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "all_short.json"
            save_json(mock_corpus, input_path)
            
            _, original, filtered = filter_short_abstracts(input_path)
            
            assert original == 2
            assert filtered == 0

    def test_missing_file(self):
        """Test that FileNotFoundError is raised if input file is missing."""
        with pytest.raises(FileNotFoundError):
            filter_short_abstracts(Path("/nonexistent/path/corpus.json"))
