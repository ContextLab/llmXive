"""
Tests for the research validator (T039).
"""
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from research_validator import parse_research_md, STATIC_URL_PATTERNS, FORBIDDEN_PATTERNS

def test_valid_research_md(tmp_path):
    """Test a valid research.md file."""
    valid_content = """
    # Research Data Sources

    ## OpenML
    - URL: https://www.openml.org/d/43845

    ## HuggingFace
    - URL: https://huggingface.co/datasets/materials-science/lst-wear-2023
    """
    file_path = tmp_path / "research.md"
    file_path.write_text(valid_content)

    is_valid, errors = parse_research_md(file_path)
    assert is_valid is True
    assert len(errors) == 0

def test_forbidden_pattern_search(tmp_path):
    """Test detection of forbidden 'search' pattern."""
    invalid_content = """
    # Research
    Use search API to find data: https://example.com/search?q=laser
    """
    file_path = tmp_path / "research.md"
    file_path.write_text(invalid_content)

    is_valid, errors = parse_research_md(file_path)
    assert is_valid is False
    assert any("Forbidden pattern" in e for e in errors)

def test_dynamic_keyword(tmp_path):
    """Test detection of dynamic keywords."""
    invalid_content = """
    # Research
    We use dynamic search to find the best dataset.
    """
    file_path = tmp_path / "research.md"
    file_path.write_text(invalid_content)

    is_valid, errors = parse_research_md(file_path)
    assert is_valid is False
    assert any("dynamic search logic" in e for e in errors)

def test_todo_placeholder(tmp_path):
    """Test detection of TODOs."""
    invalid_content = """
    # Research
    TODO: Add more datasets here.
    """
    file_path = tmp_path / "research.md"
    file_path.write_text(invalid_content)

    is_valid, errors = parse_research_md(file_path)
    assert is_valid is False
    assert any("contains TODO" in e for e in errors)

def test_invalid_url_pattern(tmp_path):
    """Test detection of invalid URL patterns."""
    invalid_content = """
    # Research
    - URL: https://example.com/dynamic/find?id=123
    """
    file_path = tmp_path / "research.md"
    file_path.write_text(invalid_content)

    is_valid, errors = parse_research_md(file_path)
    # Should fail because the URL doesn't match known static patterns
    assert is_valid is False
    assert any("does not match known static pattern" in e for e in errors)

def test_missing_file(tmp_path):
    """Test behavior when file is missing."""
    file_path = tmp_path / "nonexistent.md"
    
    is_valid, errors = parse_research_md(file_path)
    assert is_valid is False
    assert "not found" in errors[0]

def test_static_openml_url(tmp_path):
    """Test that valid OpenML URL is accepted."""
    valid_content = "URL: https://www.openml.org/d/12345"
    file_path = tmp_path / "research.md"
    file_path.write_text(valid_content)

    is_valid, errors = parse_research_md(file_path)
    assert is_valid is True

def test_static_huggingface_url(tmp_path):
    """Test that valid HuggingFace URL is accepted."""
    valid_content = "URL: https://huggingface.co/datasets/user/dataset"
    file_path = tmp_path / "research.md"
    file_path.write_text(valid_content)

    is_valid, errors = parse_research_md(file_path)
    assert is_valid is True