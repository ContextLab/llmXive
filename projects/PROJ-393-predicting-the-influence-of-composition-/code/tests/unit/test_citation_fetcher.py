"""
Unit tests for citation_fetcher.py (Task T005a).
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils.citation_fetcher import extract_citations_from_md, _normalize_crossref_response

class TestExtractCitations:
    def test_bracketed_references_single(self, tmp_path):
        content = "This is a study [1]. End."
        md_file = tmp_path / "research.md"
        md_file.write_text(content)
        
        result = extract_citations_from_md(md_file)
        assert len(result) == 1
        assert result[0]['ref_id'] == '1'
        assert result[0]['source_type'] == 'bracketed'

    def test_bracketed_references_range(self, tmp_path):
        content = "Multiple studies [1-3] are cited."
        md_file = tmp_path / "research.md"
        md_file.write_text(content)
        
        result = extract_citations_from_md(md_file)
        assert len(result) == 3
        ids = [r['ref_id'] for r in result]
        assert '1' in ids
        assert '2' in ids
        assert '3' in ids

    def test_bracketed_references_list(self, tmp_path):
        content = "See [1, 5, 8] for details."
        md_file = tmp_path / "research.md"
        md_file.write_text(content)
        
        result = extract_citations_from_md(md_file)
        assert len(result) == 3
        ids = [r['ref_id'] for r in result]
        assert '1' in ids
        assert '5' in ids
        assert '8' in ids

    def test_no_citations(self, tmp_path):
        content = "This text has no citations."
        md_file = tmp_path / "research.md"
        md_file.write_text(content)
        
        result = extract_citations_from_md(md_file)
        assert len(result) == 0

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract_citations_from_md(Path("non_existent_file.md"))

class TestNormalizeCrossref:
    def test_normalize_basic(self):
        mock_message = {
            'title': ['Test Title'],
            'DOI': '10.1234/test',
            'author': [{'given': 'John', 'family': 'Doe'}],
            'published-print': {'date-parts': [[2023, 1, 1]]},
            'container-title': ['Journal of Tests']
        }
        result = _normalize_crossref_response(mock_message)
        
        assert result['title'] == 'Test Title'
        assert result['doi'] == '10.1234/test'
        assert result['url'] == 'https://doi.org/10.1234/test'
        assert 'John Doe' in result['authors']
        assert result['year'] == 2023
        assert result['container_title'] == 'Journal of Tests'

    def test_normalize_missing_fields(self):
        mock_message = {
            'title': ['Title Only'],
            'DOI': None,
            'author': []
        }
        result = _normalize_crossref_response(mock_message)
        
        assert result['title'] == 'Title Only'
        assert result['doi'] is None
        assert result['url'] is None
        assert result['authors'] == ''
        assert result['year'] is None
