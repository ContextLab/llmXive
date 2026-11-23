"""
Unit tests for causal language linting utilities.

These tests verify that the linter correctly identifies causal language
and allows non-causal language to pass.
"""

import pytest
import tempfile
import os
from pathlib import Path

from utils.linters import (
    check_text_for_causal_claims,
    lint_report_file,
    lint_multiple_files,
    fail_build_on_causal_claims,
    CAUSAL_TERMS
)
from utils.logger import get_logger


class TestCausalTermDetection:
    """Tests for basic causal term detection."""

    def test_detects_simple_causal_term(self):
        """Test that simple causal terms are detected."""
        text = "This model causes significant performance improvements."
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is True
        assert result['count'] == 1
        assert any(m['term'].lower() == 'causes' for m in result['matches'])

    def test_detects_proves(self):
        """Test that 'proves' is detected."""
        text = "The results prove our hypothesis."
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is True
        assert result['count'] == 1

    def test_detects_determines(self):
        """Test that 'determines' is detected."""
        text = "Temperature determines the reaction rate."
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is True
        assert result['count'] == 1

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        text = "This CAUSES problems. This Proves it. This DETERMINES the outcome."
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is True
        assert result['count'] == 3

    def test_multiple_occurrences(self):
        """Test detection of multiple occurrences of the same term."""
        text = "This causes issues. That also causes problems."
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is True
        assert result['count'] == 2

    def test_no_false_positives_for_non_causal(self):
        """Test that non-causal language passes."""
        text = (
            "The model shows improved performance. "
            "There is a correlation between variables. "
            "The data suggests a relationship."
        )
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is False
        assert result['count'] == 0

    def test_word_boundaries(self):
        """Test that only whole words are matched."""
        text = "The procasual process is not causal."
        result = check_text_for_causal_claims(text)

        # Should only match 'causal' as a whole word
        assert result['count'] == 1
        assert result['matches'][0]['term'].lower() == 'causal'

    def test_context_extraction(self):
        """Test that context is properly extracted."""
        text = "This is a long sentence. " + "causes" + " is in the middle."
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is True
        assert len(result['matches']) == 1
        assert 'causes' in result['matches'][0]['context']


class TestFileLinting:
    """Tests for file-based linting."""

    @pytest.fixture
    def temp_text_file(self, tmp_path):
        """Create a temporary text file with causal language."""
        file_path = tmp_path / "test_report.txt"
        file_path.write_text("This model causes better results.")
        return file_path

    @pytest.fixture
    def temp_clean_file(self, tmp_path):
        """Create a temporary text file without causal language."""
        file_path = tmp_path / "clean_report.txt"
        file_path.write_text(
            "This model shows improved results. "
            "There is an association between variables."
        )
        return file_path

    def test_lint_file_with_causal_language(self, temp_text_file):
        """Test linting a file with causal language."""
        result = lint_report_file(temp_text_file)

        assert result['passed'] is False
        assert result['has_causal_claims'] is True
        assert result['count'] == 1

    def test_lint_file_without_causal_language(self, temp_clean_file):
        """Test linting a file without causal language."""
        result = lint_report_file(temp_clean_file)

        assert result['passed'] is True
        assert result['has_causal_claims'] is False
        assert result['count'] == 0

    def test_lint_nonexistent_file(self, tmp_path):
        """Test linting a file that doesn't exist."""
        file_path = tmp_path / "nonexistent.txt"

        result = lint_report_file(file_path)

        assert result['passed'] is False
        assert result['error_message'] is not None
        assert "not found" in result['error_message'].lower()

    def test_lint_multiple_files(self, tmp_path):
        """Test linting multiple files."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("This causes issues.")

        file2 = tmp_path / "file2.txt"
        file2.write_text("This shows correlation.")

        file3 = tmp_path / "file3.txt"
        file3.write_text("That proves the point.")

        result = lint_multiple_files([file1, file2, file3])

        assert result['total_files'] == 3
        assert result['passed'] == 1
        assert result['failed'] == 2
        assert result['total_causal_claims'] == 2
        assert result['overall_passed'] is False


class TestBuildFailure:
    """Tests for build failure on causal language."""

    def test_fail_build_on_causal_claims_raises(self, tmp_path):
        """Test that fail_build_on_causal_claims raises on causal language."""
        file_path = tmp_path / "bad_report.txt"
        file_path.write_text("This causes problems.")

        with pytest.raises(ValueError) as excinfo:
            fail_build_on_causal_claims([file_path])

        assert "BUILD FAILED" in str(excinfo.value)
        assert "causes" in str(excinfo.value).lower()

    def test_fail_build_on_causal_claims_passes_clean(self, tmp_path):
        """Test that clean files don't raise."""
        file_path = tmp_path / "good_report.txt"
        file_path.write_text("This shows correlation.")

        # Should not raise
        fail_build_on_causal_claims([file_path])


class TestCausalTermsList:
    """Tests for the causal terms list."""

    def test_all_terms_are_strings(self):
        """Test that all terms in CAUSAL_TERMS are strings."""
        for term in CAUSAL_TERMS:
            assert isinstance(term, str)
            assert len(term) > 0

    def test_no_empty_terms(self):
        """Test that there are no empty terms."""
        assert "" not in CAUSAL_TERMS

    def test_common_causal_terms_present(self):
        """Test that common causal terms are in the list."""
        expected_terms = ["causes", "proves", "determines", "leads to"]
        for term in expected_terms:
            assert term in CAUSAL_TERMS


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_text(self):
        """Test handling of empty text."""
        result = check_text_for_causal_claims("")

        assert result['has_causal_claims'] is False
        assert result['count'] == 0

    def test_none_text(self):
        """Test handling of None text."""
        result = check_text_for_causal_claims(None)

        assert result['has_causal_claims'] is False
        assert result['count'] == 0

    def test_whitespace_only(self):
        """Test handling of whitespace-only text."""
        result = check_text_for_causal_claims("   \n\t  ")

        assert result['has_causal_claims'] is False
        assert result['count'] == 0

    def test_very_long_text(self, tmp_path):
        """Test handling of very long text."""
        long_text = "This causes issues. " * 1000
        result = check_text_for_causal_claims(long_text)

        assert result['has_causal_claims'] is True
        assert result['count'] == 1000

    def test_special_characters(self):
        """Test handling of special characters in text."""
        text = "This causes! problems? Yes, causes."
        result = check_text_for_causal_claims(text)

        assert result['has_causal_claims'] is True
        assert result['count'] == 2