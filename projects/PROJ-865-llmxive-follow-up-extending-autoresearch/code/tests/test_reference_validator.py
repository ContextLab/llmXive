"""
Tests for the Reference Validator Agent.

These tests validate the citation validation logic without requiring
actual network access or a research.md file.
"""
import json
import sys
import os
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.reference_validator import (
    extract_citations_from_markdown,
    validate_url_reachability,
    validate_citation_citation_mismatch,
    run_citation_validation
)

class TestCitationExtraction:
    """Tests for citation extraction from markdown."""

    def test_inline_citations(self):
        """Test extraction of inline citations [label](url)."""
        markdown = """
        This is a sentence with a citation [Paper Title](https://arxiv.org/abs/1234.5678).
        Another citation here [Another Paper](https://github.com/user/repo).
        """
        
        citations = extract_citations_from_markdown(markdown)
        
        assert len(citations) == 2
        assert citations[0]['label'] == 'Paper Title'
        assert citations[0]['url'] == 'https://arxiv.org/abs/1234.5678'
        assert citations[0]['type'] == 'inline'
        assert citations[1]['label'] == 'Another Paper'
        assert citations[1]['url'] == 'https://github.com/user/repo'
        assert citations[1]['type'] == 'inline'

    def test_reference_citations(self):
        """Test extraction of reference-style citations."""
        markdown = """
        This is a citation [Paper Title][paper1].
        And another [Another Paper][paper2].
        
        [paper1]: https://arxiv.org/abs/1234.5678
        [paper2]: https://github.com/user/repo
        """
        
        citations = extract_citations_from_markdown(markdown)
        
        assert len(citations) == 2
        assert citations[0]['label'] == 'Paper Title'
        assert citations[0]['url'] == 'https://arxiv.org/abs/1234.5678'
        assert citations[0]['type'] == 'reference'
        assert citations[1]['label'] == 'Another Paper'
        assert citations[1]['url'] == 'https://github.com/user/repo'
        assert citations[1]['type'] == 'reference'

    def test_mixed_citations(self):
        """Test extraction of mixed citation styles."""
        markdown = """
        Inline [Paper](https://arxiv.org/abs/1234.5678) and reference [Another][ref1].
        
        [ref1]: https://github.com/user/repo
        """
        
        citations = extract_citations_from_markdown(markdown)
        
        assert len(citations) == 2
        assert citations[0]['type'] == 'inline'
        assert citations[1]['type'] == 'reference'

    def test_empty_markdown(self):
        """Test extraction from empty markdown."""
        markdown = ""
        citations = extract_citations_from_markdown(markdown)
        assert len(citations) == 0

    def test_no_citations(self):
        """Test extraction from markdown without citations."""
        markdown = """
        This is just plain text without any citations.
        """
        citations = extract_citations_from_markdown(markdown)
        assert len(citations) == 0


class TestUrlValidation:
    """Tests for URL reachability validation."""

    def test_valid_arxiv_url(self):
        """Test validation of a valid arXiv URL."""
        is_valid, error = validate_url_reachability("https://arxiv.org/abs/1234.5678")
        assert is_valid is True
        assert error is None

    def test_valid_github_url(self):
        """Test validation of a valid GitHub URL."""
        is_valid, error = validate_url_reachability("https://github.com/user/repo")
        assert is_valid is True
        assert error is None

    def test_valid_huggingface_url(self):
        """Test validation of a valid Hugging Face URL."""
        is_valid, error = validate_url_reachability("https://huggingface.co/model")
        assert is_valid is True
        assert error is None

    def test_invalid_url_format(self):
        """Test validation of an invalid URL format."""
        is_valid, error = validate_url_reachability("not-a-valid-url")
        assert is_valid is False
        assert "Invalid URL format" in error

    def test_missing_scheme(self):
        """Test validation of a URL missing scheme."""
        is_valid, error = validate_url_reachability("arxiv.org/abs/1234.5678")
        assert is_valid is False
        assert "Invalid URL format" in error

    def test_missing_netloc(self):
        """Test validation of a URL missing network location."""
        is_valid, error = validate_url_reachability("https://")
        assert is_valid is False
        assert "Invalid URL format" in error


class TestCitationMismatch:
    """Tests for citation mismatch detection."""

    def test_no_mismatches(self):
        """Test when there are no mismatches."""
        citations = [
            {'label': 'Paper1', 'url': 'https://arxiv.org/abs/1234.5678', 'line_number': 1, 'type': 'inline'},
            {'label': 'Paper2', 'url': 'https://github.com/user/repo', 'line_number': 2, 'type': 'inline'},
        ]
        
        mismatches = validate_citation_citation_mismatch(citations, "")
        assert len(mismatches) == 0

    def test_duplicate_different_urls(self):
        """Test detection of duplicate citations with different URLs."""
        citations = [
            {'label': 'Paper1', 'url': 'https://arxiv.org/abs/1234.5678', 'line_number': 1, 'type': 'inline'},
            {'label': 'Paper1', 'url': 'https://arxiv.org/abs/8765.4321', 'line_number': 5, 'type': 'inline'},
        ]
        
        mismatches = validate_citation_citation_mismatch(citations, "")
        assert len(mismatches) == 1
        assert mismatches[0]['label'] == 'Paper1'
        assert 'different URLs' in mismatches[0]['details']

    def test_same_url_duplicate(self):
        """Test that same URL duplicates don't trigger mismatch."""
        citations = [
            {'label': 'Paper1', 'url': 'https://arxiv.org/abs/1234.5678', 'line_number': 1, 'type': 'inline'},
            {'label': 'Paper1', 'url': 'https://arxiv.org/abs/1234.5678', 'line_number': 5, 'type': 'inline'},
        ]
        
        mismatches = validate_citation_citation_mismatch(citations, "")
        assert len(mismatches) == 0


class TestFullValidation:
    """Tests for the full validation pipeline."""

    def test_missing_research_file(self):
        """Test validation when research.md doesn't exist."""
        # This test assumes research.md doesn't exist in the test environment
        result = run_citation_validation()
        assert result['status'] == 'FAIL'
        assert 'Research file not found' in result.get('error', '')

    def test_empty_research_file(self, tmp_path):
        """Test validation with an empty research.md file."""
        # Create a temporary research.md file
        research_file = tmp_path / "research.md"
        research_file.write_text("")
        
        # Temporarily change the path
        import utils.reference_validator as validator_module
        original_path = validator_module.RESEARCH_MD_PATH
        validator_module.RESEARCH_MD_PATH = research_file
        
        try:
            result = run_citation_validation()
            assert result['status'] == 'PASS'
            assert result['citations_checked'] == 0
            assert result['valid_citations'] == 0
            assert result['invalid_citations'] == 0
        finally:
            # Restore original path
            validator_module.RESEARCH_MD_PATH = original_path

    def test_valid_research_file(self, tmp_path):
        """Test validation with a valid research.md file."""
        # Create a temporary research.md file with valid citations
        research_content = """
        # Research Paper
        
        This is a citation [Paper](https://arxiv.org/abs/1234.5678).
        """
        research_file = tmp_path / "research.md"
        research_file.write_text(research_content)
        
        # Temporarily change the path
        import utils.reference_validator as validator_module
        original_path = validator_module.RESEARCH_MD_PATH
        original_output_path = validator_module.OUTPUT_REPORT_PATH
        validator_module.RESEARCH_MD_PATH = research_file
        validator_module.OUTPUT_REPORT_PATH = tmp_path / "report.json"
        
        try:
            result = run_citation_validation()
            assert result['status'] == 'PASS'
            assert result['citations_checked'] == 1
            assert result['valid_citations'] == 1
            assert result['invalid_citations'] == 0
            
            # Verify the report file was created
            assert validator_module.OUTPUT_REPORT_PATH.exists()
            with open(validator_module.OUTPUT_REPORT_PATH, 'r') as f:
                report = json.load(f)
            assert report['status'] == 'PASS'
        finally:
            # Restore original paths
            validator_module.RESEARCH_MD_PATH = original_path
            validator_module.OUTPUT_REPORT_PATH = original_output_path

    def test_invalid_citations(self, tmp_path):
        """Test validation with invalid citations."""
        # Create a temporary research.md file with invalid citations
        research_content = """
        # Research Paper
        
        This is an invalid citation [Paper](not-a-valid-url).
        """
        research_file = tmp_path / "research.md"
        research_file.write_text(research_content)
        
        # Temporarily change the path
        import utils.reference_validator as validator_module
        original_path = validator_module.RESEARCH_MD_PATH
        original_output_path = validator_module.OUTPUT_REPORT_PATH
        validator_module.RESEARCH_MD_PATH = research_file
        validator_module.OUTPUT_REPORT_PATH = tmp_path / "report.json"
        
        try:
            result = run_citation_validation()
            assert result['status'] == 'FAIL'
            assert result['citations_checked'] == 1
            assert result['valid_citations'] == 0
            assert result['invalid_citations'] == 1
        finally:
            # Restore original paths
            validator_module.RESEARCH_MD_PATH = original_path
            validator_module.OUTPUT_REPORT_PATH = original_output_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])