"""
Unit tests for citation schema validation module.

Tests for src/utils/citation_schema.py to ensure pre-validation
of citation metadata works correctly (Constitution II).
"""

import pytest
from src.utils.citation_schema import (
    validate_citation_entry,
    validate_citation_list,
    get_required_fields,
    validate_citation_entry_strict,
    REQUIRED_CITATION_FIELDS
)


class TestCitationSchemaValidation:
    """Test suite for citation schema validation functions."""

    def test_get_required_fields(self):
        """Test that required fields are returned correctly."""
        fields = get_required_fields()
        assert isinstance(fields, list)
        assert len(fields) == 4
        assert 'title' in fields
        assert 'authors' in fields
        assert 'year' in fields
        assert 'doi' in fields
        assert fields == REQUIRED_CITATION_FIELDS

    def test_validate_citation_entry_valid(self):
        """Test validation of a complete, valid citation entry."""
        entry = {
            'title': 'Test Title',
            'authors': ['Author One', 'Author Two'],
            'year': 2023,
            'doi': '10.1234/test.12345'
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is True
        assert missing == []

    def test_validate_citation_entry_missing_title(self):
        """Test validation when title is missing."""
        entry = {
            'authors': ['Author One'],
            'year': 2023,
            'doi': '10.1234/test.12345'
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is False
        assert 'title' in missing

    def test_validate_citation_entry_missing_authors(self):
        """Test validation when authors is missing."""
        entry = {
            'title': 'Test Title',
            'year': 2023,
            'doi': '10.1234/test.12345'
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is False
        assert 'authors' in missing

    def test_validate_citation_entry_missing_year(self):
        """Test validation when year is missing."""
        entry = {
            'title': 'Test Title',
            'authors': ['Author One'],
            'doi': '10.1234/test.12345'
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is False
        assert 'year' in missing

    def test_validate_citation_entry_missing_doi(self):
        """Test validation when doi is missing."""
        entry = {
            'title': 'Test Title',
            'authors': ['Author One'],
            'year': 2023
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is False
        assert 'doi' in missing

    def test_validate_citation_entry_multiple_missing(self):
        """Test validation when multiple fields are missing."""
        entry = {
            'title': 'Test Title'
            # Missing authors, year, doi
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is False
        assert len(missing) == 3
        assert 'authors' in missing
        assert 'year' in missing
        assert 'doi' in missing

    def test_validate_citation_entry_empty_string_fields(self):
        """Test validation when fields are empty strings."""
        entry = {
            'title': '',
            'authors': [],
            'year': None,
            'doi': ''
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is False
        assert len(missing) == 4

    def test_validate_citation_entry_whitespace_string(self):
        """Test validation when string fields are whitespace only."""
        entry = {
            'title': '   ',
            'authors': ['Author'],
            'year': 2023,
            'doi': '   '
        }
        
        is_valid, missing = validate_citation_entry(entry)
        
        assert is_valid is False
        assert 'title' in missing
        assert 'doi' in missing

    def test_validate_citation_entry_non_dict_input(self):
        """Test validation raises TypeError for non-dict input."""
        with pytest.raises(TypeError):
            validate_citation_entry("not a dict")
        
        with pytest.raises(TypeError):
            validate_citation_entry(["list", "of", "items"])
        
        with pytest.raises(TypeError):
            validate_citation_entry(None)

    def test_validate_citation_list_all_valid(self):
        """Test list validation when all entries are valid."""
        citations = [
            {
                'title': 'Title 1',
                'authors': ['A'],
                'year': 2020,
                'doi': '10.1/1'
            },
            {
                'title': 'Title 2',
                'authors': ['B'],
                'year': 2021,
                'doi': '10.1/2'
            }
        ]
        
        all_valid, report = validate_citation_list(citations)
        
        assert all_valid is True
        assert report['total_count'] == 2
        assert report['valid_count'] == 2
        assert report['invalid_count'] == 0
        assert report['invalid_entries'] == []

    def test_validate_citation_list_mixed_validity(self):
        """Test list validation with mixed valid/invalid entries."""
        citations = [
            {
                'title': 'Valid',
                'authors': ['A'],
                'year': 2020,
                'doi': '10.1/1'
            },
            {
                'title': 'Invalid'
                # Missing authors, year, doi
            },
            {
                'title': 'Valid 2',
                'authors': ['B'],
                'year': 2021,
                'doi': '10.1/2'
            }
        ]
        
        all_valid, report = validate_citation_list(citations)
        
        assert all_valid is False
        assert report['total_count'] == 3
        assert report['valid_count'] == 2
        assert report['invalid_count'] == 1
        assert len(report['invalid_entries']) == 1
        assert report['invalid_entries'][0]['index'] == 1
        assert len(report['invalid_entries'][0]['missing_fields']) == 3

    def test_validate_citation_list_empty(self):
        """Test list validation with empty list."""
        all_valid, report = validate_citation_list([])
        
        assert all_valid is True
        assert report['total_count'] == 0
        assert report['valid_count'] == 0
        assert report['invalid_count'] == 0

    def test_validate_citation_list_non_dict_in_list(self):
        """Test list validation raises TypeError if list contains non-dict."""
        citations = [
            {'title': 'Valid', 'authors': ['A'], 'year': 2020, 'doi': '10.1/1'},
            "not a dict"
        ]
        
        with pytest.raises(TypeError):
            validate_citation_list(citations)

    def test_validate_citation_entry_strict_valid(self):
        """Test strict validation passes for valid entry."""
        entry = {
            'title': 'Valid Title',
            'authors': ['Author'],
            'year': 2023,
            'doi': '10.1234/test'
        }
        
        # Should not raise
        validate_citation_entry_strict(entry)

    def test_validate_citation_entry_strict_invalid(self):
        """Test strict validation raises ValueError for invalid entry."""
        entry = {
            'title': 'Missing Fields',
            'authors': ['Author']
            # Missing year, doi
        }
        
        with pytest.raises(ValueError) as exc_info:
            validate_citation_entry_strict(entry)
        
        assert 'missing required fields' in str(exc_info.value).lower()
        assert 'year' in str(exc_info.value)
        assert 'doi' in str(exc_info.value)

    def test_validate_citation_entry_strict_empty_fields(self):
        """Test strict validation raises for empty/whitespace fields."""
        entry = {
            'title': '   ',
            'authors': ['Author'],
            'year': 2023,
            'doi': '10.1234/test'
        }
        
        with pytest.raises(ValueError):
            validate_citation_entry_strict(entry)