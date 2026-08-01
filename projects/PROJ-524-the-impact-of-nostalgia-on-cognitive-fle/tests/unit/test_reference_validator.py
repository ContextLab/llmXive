"""
Unit tests for code/reference_validator.py citation validation functions.
"""
import pytest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.reference_validator import (
    normalize_text,
    calculate_title_overlap,
    load_references_from_file
)


class TestNormalizeText:
    def test_normalize_lowercase(self):
        """Test text normalization to lowercase."""
        text = "The Quick Brown Fox"
        result = normalize_text(text)
        assert result == "the quick brown fox"

    def test_normalize_remove_punctuation(self):
        """Test punctuation removal."""
        text = "Hello, World! How are you?"
        result = normalize_text(text)
        assert "," not in result
        assert "!" not in result
        assert "?" not in result

    def test_normalize_extra_spaces(self):
        """Test extra space removal."""
        text = "Hello   World   Test"
        result = normalize_text(text)
        assert "   " not in result
        assert result == "hello world test"

    def test_normalize_empty_string(self):
        """Test empty string handling."""
        result = normalize_text("")
        assert result == ""


class TestTitleOverlap:
    def test_calculate_title_overlap_identical(self):
        """Test overlap calculation for identical titles."""
        title1 = "The Impact of Nostalgia on Cognitive Flexibility"
        title2 = "The Impact of Nostalgia on Cognitive Flexibility"

        overlap = calculate_title_overlap(title1, title2)
        assert overlap == 1.0

    def test_calculate_title_overlap_none(self):
        """Test overlap calculation for completely different titles."""
        title1 = "Nostalgia and Memory"
        title2 = "Climate Change Effects"

        overlap = calculate_title_overlap(title1, title2)
        assert overlap == 0.0

    def test_calculate_title_overlap_partial(self):
        """Test overlap calculation for partially similar titles."""
        title1 = "Nostalgia Effects on Aging Adults"
        title2 = "Cognitive Effects of Nostalgia in Aging"

        overlap = calculate_title_overlap(title1, title2)
        assert 0 < overlap < 1.0

    def test_calculate_title_overlap_case_insensitive(self):
        """Test that overlap calculation is case insensitive."""
        title1 = "The Impact of Nostalgia"
        title2 = "THE IMPACT OF NOSTALGIA"

        overlap = calculate_title_overlap(title1, title2)
        assert overlap == 1.0

    def test_calculate_title_overlap_empty(self):
        """Test overlap calculation with empty strings."""
        overlap = calculate_title_overlap("", "")
        assert overlap == 0.0


class TestLoadReferencesFromFile:
    def test_load_references_json(self):
        """Test loading references from JSON file."""
        test_data = [
            {"title": "Study One", "authors": ["Author A"], "year": 2020},
            {"title": "Study Two", "authors": ["Author B"], "year": 2021}
        ]

        with patch('code.reference_validator.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.read_text.return_value = json.dumps(test_data)
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            result = load_references_from_file(Path("test.json"))
            assert len(result) == 2
            assert result[0]['title'] == "Study One"

    def test_load_references_empty_file(self):
        """Test loading from empty JSON file."""
        with patch('code.reference_validator.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.read_text.return_value = "[]"
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            result = load_references_from_file(Path("empty.json"))
            assert len(result) == 0

    def test_load_references_invalid_json(self):
        """Test loading from invalid JSON file."""
        with patch('code.reference_validator.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.read_text.return_value = "{invalid json}"
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            with pytest.raises(json.JSONDecodeError):
                load_references_from_file(Path("invalid.json"))
