"""
Unit tests for verify_exclusion_citations.py

Tests the logic of parsing the research draft and verifying exclusion citations.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module functions (adjust path if needed)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.verify_exclusion_citations import (
    find_methods_section,
    check_citation_in_text,
    main
)


class TestFindMethodsSection:
    """Tests for find_methods_section function."""

    def test_find_methods_section_simple(self):
        """Test finding a simple Methods section."""
        text = """
        # Introduction
        Some text.

        # Methods
        This is the methods section content.
        More text here.

        # Results
        Results content.
        """
        result = find_methods_section(text)
        assert result is not None
        assert "methods section content" in result.lower()

    def test_find_methods_section_with_subheaders(self):
        """Test finding Methods section with subheaders."""
        text = """
        # Methods
        ## Data Collection
        We collected data.
        ## Analysis
        We analyzed data.
        """
        result = find_methods_section(text)
        assert result is not None
        assert "data collection" in result.lower()
        assert "analysis" in result.lower()

    def test_find_methods_section_not_found(self):
        """Test when Methods section is missing."""
        text = """
        # Introduction
        Some text.

        # Results
        Results content.
        """
        result = find_methods_section(text)
        assert result is None

    def test_find_methods_section_case_insensitive(self):
        """Test case insensitivity."""
        text = """
        # methods
        Lowercase methods section.
        """
        result = find_methods_section(text)
        assert result is not None
        assert "lowercase methods section" in result.lower()


class TestCheckCitationInText:
    """Tests for check_citation_in_text function."""

    def test_citation_found_memory_keyword(self):
        """Test that memory keyword is detected."""
        text = "We excluded models based on memory constraints."
        result = check_citation_in_text(text)
        assert result["citation_found"] is True
        assert "memory" in result["keywords_found"]

    def test_citation_found_ram_keyword(self):
        """Test that RAM keyword is detected."""
        text = "RAM usage was monitored to exclude large models."
        result = check_citation_in_text(text)
        assert result["citation_found"] is True
        assert "ram" in result["keywords_found"]

    def test_citation_found_exclusion_keyword(self):
        """Test that exclusion keyword is detected."""
        text = "Exclusion criteria were applied to the dataset."
        result = check_citation_in_text(text)
        assert result["citation_found"] is True
        assert "exclusion" in result["keywords_found"]

    def test_citation_found_scope_adjustment_keyword(self):
        """Test that scope_adjustment keyword is detected."""
        text = "Scope adjustments were made based on model limitations."
        result = check_citation_in_text(text)
        assert result["citation_found"] is True
        assert "scope" in result["keywords_found"]

    def test_citation_not_found(self):
        """Test when no keywords are found."""
        text = "This is a generic paragraph with no relevant keywords."
        result = check_citation_in_text(text)
        assert result["citation_found"] is False
        assert len(result["keywords_found"]) == 0

    def test_excerpt_generation(self):
        """Test that excerpt is generated around keyword."""
        text = "We performed extensive memory profiling to ensure compliance."
        result = check_citation_in_text(text)
        assert result["citation_found"] is True
        assert result["excerpt"] is not None
        assert "memory" in result["excerpt"].lower()


class TestMain:
    """Tests for the main function."""

    @patch("code.analysis.verify_exclusion_citations.ensure_directories")
    @patch("code.analysis.verify_exclusion_citations.DRAFT_PATH")
    @patch("code.analysis.verify_exclusion_citations.OUTPUT_PATH")
    def test_main_draft_not_found(self, mock_output, mock_draft, mock_ensure):
        """Test main when draft file is not found."""
        mock_draft.exists.return_value = False
        mock_output.parent = Path("data/results")
        mock_output.parent.mkdir = Path.mkdir

        # Mock open to raise FileNotFoundError
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = main()
            assert result == 1  # Error code

        # Verify output was written
        mock_output.parent.mkdir.assert_called_once()

    @patch("code.analysis.verify_exclusion_citations.ensure_directories")
    @patch("code.analysis.verify_exclusion_citations.DRAFT_PATH")
    @patch("code.analysis.verify_exclusion_citations.OUTPUT_PATH")
    def test_main_successful_citation(self, mock_output, mock_draft, mock_ensure):
        """Test main when citation is found."""
        mock_draft.exists.return_value = True
        mock_draft.read_text.return_value = """
        # Methods
        We excluded models based on memory constraints (T009, T041).
        """
        mock_output.parent = Path("data/results")
        mock_output.parent.mkdir = Path.mkdir

        with patch("builtins.open", mock_open_read_data=mock_draft.read_text):
            result = main()
            assert result == 0  # Success

    @patch("code.analysis.verify_exclusion_citations.ensure_directories")
    @patch("code.analysis.verify_exclusion_citations.DRAFT_PATH")
    @patch("code.analysis.verify_exclusion_citations.OUTPUT_PATH")
    def test_main_no_citation(self, mock_output, mock_draft, mock_ensure):
        """Test main when no citation is found."""
        mock_draft.exists.return_value = True
        mock_draft.read_text.return_value = """
        # Methods
        This is a generic methods section without exclusion references.
        """
        mock_output.parent = Path("data/results")
        mock_output.parent.mkdir = Path.mkdir

        with patch("builtins.open", mock_open_read_data=mock_draft.read_text):
            result = main()
            assert result == 0  # Spec says return 0 even if warning