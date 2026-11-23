"""
Unit tests for T014c: filter_human_confirmations.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.src.extraction.filter_human_confirmations import (
    find_confirmation_type,
    extract_location_from_comment,
    filter_confirmations,
    CONFIRMATION_PHRASES
)


class TestFindConfirmationType:
    """Test the rubric matching logic."""

    def test_exact_match(self):
        assert find_confirmation_type("Bug confirmed here") == "bug confirmed"

    def test_case_insensitive(self):
        assert find_confirmation_type("BUG CONFIRMED") == "bug confirmed"
        assert find_confirmation_type("Bug Confirmed") == "bug confirmed"

    def test_partial_match(self):
        assert find_confirmation_type("This is a bug confirmed by me") == "bug confirmed"

    def test_multiple_phrases(self):
        # Should return the first match found in the list order
        text = "Bug confirmed and merged with fix"
        result = find_confirmation_type(text)
        assert result in ["bug confirmed", "merged with fix"]

    def test_no_match(self):
        assert find_confirmation_type("LGTM") is None
        assert find_confirmation_type("Looks good") is None
        assert find_confirmation_type("") is None

    def test_all_phrases(self):
        for phrase in CONFIRMATION_PHRASES:
            # Ensure each phrase can be detected
            assert find_confirmation_type(phrase) == phrase
            assert find_confirmation_type(f"Comment: {phrase.upper()}") == phrase


class TestExtractLocationFromComment:
    """Test location extraction logic."""

    def test_standard_review_comment(self):
        comment = {
            "path": "src/main.py",
            "line": 42
        }
        fp, start, end = extract_location_from_comment(comment)
        assert fp == "src/main.py"
        assert start == 42
        assert end == 42

    def test_with_position_instead_of_line(self):
        comment = {
            "path": "src/utils.py",
            "position": 10
        }
        fp, start, end = extract_location_from_comment(comment)
        assert fp == "src/utils.py"
        assert start == 10
        assert end == 10

    def test_original_and_current_line(self):
        comment = {
            "path": "src/test.py",
            "original_line": 5,
            "current_line": 6
        }
        fp, start, end = extract_location_from_comment(comment)
        # Logic: if 'line' is missing but 'original_line' exists, use it
        # Note: Our implementation checks 'line' first, then 'original_line'
        # If 'line' is None, it falls back to original_line
        assert fp == "src/test.py"
        # Depending on exact implementation:
        # if line is missing, we use original_line
        assert start == 5
        assert end == 6

    def test_missing_location(self):
        comment = {
            "body": "LGTM"
        }
        fp, start, end = extract_location_from_comment(comment)
        assert fp is None
        assert start is None
        assert end is None


class TestFilterConfirmations:
    """Test the full filtering pipeline with mock data."""

    @pytest.fixture
    def mock_raw_data(self):
        return {
            "prs": [
                {
                    "pr_id": 101,
                    "comments": [
                        {
                            "reviewer_id": "user_a",
                            "body": "Bug confirmed in this section.",
                            "path": "file.py",
                            "line": 10
                        },
                        {
                            "reviewer_id": "user_b",
                            "body": "LGTM, looks good to me.",
                            "path": "file.py",
                            "line": 15
                        },
                        {
                            "reviewer_id": "user_c",
                            "body": "Merged with fix.",
                            "path": "utils.py",
                            "line": 20
                        },
                        {
                            "reviewer_id": "user_d",
                            "body": "Verified the fix.",
                            "path": "main.py",
                            "original_line": 30,
                            "current_line": 32
                        }
                    ]
                },
                {
                    "pr_id": 102,
                    "comments": [
                        {
                            "reviewer_id": "user_e",
                            "body": "No issues found."
                        }
                    ]
                }
            ]
        }

    def test_filter_logic(self, mock_raw_data, tmp_path):
        input_file = tmp_path / "raw_comments.json"
        output_file = tmp_path / "human_confirmations.json"

        input_file.write_text(json.dumps(mock_raw_data))

        # Patch get_paths to use tmp_path
        with patch("code.src.extraction.filter_human_confirmations.get_paths") as mock_get_paths:
            mock_get_paths.return_value = {
                "annotations_raw": input_file,
                "derived_human_confirmations": output_file
            }
            with patch("code.src.extraction.filter_human_confirmations.ensure_directories"):
                from code.src.extraction.filter_human_confirmations import filter_confirmations, save_confirmations

                confirmations = filter_confirmations(input_file)
                save_confirmations(confirmations, output_file)

        # Verify results
        assert len(confirmations) == 3  # user_a, user_c, user_d

        # Check specific fields
        found_ids = {c["reviewer_id"] for c in confirmations}
        assert "user_a" in found_ids
        assert "user_c" in found_ids
        assert "user_d" in found_ids
        assert "user_b" not in found_ids  # LGTM without fix

        # Check types
        for c in confirmations:
            assert isinstance(c["pr_id"], int)
            assert isinstance(c["file_path"], str)
            assert isinstance(c["line_start"], int)
            assert isinstance(c["line_end"], int)
            assert isinstance(c["reviewer_id"], str)
            assert isinstance(c["confirmation_type"], str)

    def test_missing_input_file(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.json"
        with pytest.raises(FileNotFoundError):
            filter_confirmations(non_existent)