"""
Unit tests for validate_citations.py
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add the project root to the path if running directly
# In a real test runner, this should be handled by the environment
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cli.validate_citations import extract_citations, extract_bibliography, validate_citations

class TestCitationExtraction:
    def test_extract_numeric_citations(self):
        text = "This is a statement [1] and another [2]. See also [1]."
        citations = extract_citations(text)
        assert '1' in citations
        assert '2' in citations
        assert len(citations) == 2

    def test_extract_author_year_citations(self):
        text = "Smith (2020) found that Jones, (2021) disagreed."
        citations = extract_citations(text)
        # The regex captures (Author, Year) or Author (Year)
        # "Smith 2020" and "Jones 2021" should be found
        assert any('smith' in c.lower() for c in citations)
        assert any('jones' in c.lower() for c in citations)

class TestBibliographyExtraction:
    def test_extract_simple_bibliography(self):
        text = """
        Introduction
        ...
        References:
        [1] Smith, J. (2020). Title A.
        [2] Jones, B. (2021). Title B.
        """
        bib = extract_bibliography(text)
        assert '1' in bib
        assert '2' in bib
        assert 'Smith' in bib['1']
        assert 'Jones' in bib['2']

class TestValidation:
    def test_valid_citations(self):
        citations = ['1', '2']
        bibliography = {
            '1': 'Smith, J. (2020). Title A.',
            '2': 'Jones, B. (2021). Title B.'
        }
        is_valid, invalid = validate_citations(citations, bibliography)
        assert is_valid
        assert len(invalid) == 0

    def test_invalid_citations(self):
        citations = ['1', '99']
        bibliography = {
            '1': 'Smith, J. (2020). Title A.'
        }
        is_valid, invalid = validate_citations(citations, bibliography)
        assert not is_valid
        assert '99' in invalid
