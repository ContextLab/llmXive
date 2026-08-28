"""
Unit tests for the citation extraction utility.
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from utils.citation_extractor import extract_citations_from_text, parse_markdown_file

def test_extract_dois():
    text = "See the study at 10.1038/s41586-020-2649-2 for details. Also check 10.1109/ICSE.2021.00012."
    citations = extract_citations_from_text(text, "test")
    doi_ids = [c['id'] for c in citations]
    assert "10.1038/s41586-020-2649-2" in doi_ids
    assert "10.1109/ICSE.2021.00012" in doi_ids

def test_extract_urls():
    text = "Read more at https://example.com/paper and http://github.com/user/repo."
    citations = extract_citations_from_text(text, "test")
    urls = [c['url'] for c in citations]
    assert "https://example.com/paper" in urls
    assert "http://github.com/user/repo" in urls

def test_deduplication():
    text = "Check 10.1038/s41586-020-2649-2 again. Also https://example.com/paper and https://example.com/paper."
    citations = extract_citations_from_text(text, "test")
    # Should have 2 unique citations
    assert len(citations) == 2

def test_parse_file(tmp_path):
    # Create a temporary markdown file
    test_file = tmp_path / "test.md"
    test_content = "# Test\nReference: 10.1234/test. URL: https://test.org/data"
    test_file.write_text(test_content)
    
    citations = parse_markdown_file(test_file)
    assert len(citations) == 2
    assert any(c['id'] == "10.1234/test" for c in citations)
    assert any(c['url'] == "https://test.org/data" for c in citations)
