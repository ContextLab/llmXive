"""
Unit tests for citation verification functionality.
"""
import os
import tempfile
from pathlib import Path
import yaml
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from verify_citations import (
    extract_citations,
    verify_citation,
    find_artifacts,
    verify_all_citations
)

class TestExtractCitations:
    def test_markdown_links(self):
        """Test extraction of markdown links."""
        content = """
        # Test Document
        
        Check out [Google](https://www.google.com) and [GitHub](https://github.com).
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            citations = extract_citations(temp_path)
            assert len(citations) == 2
            assert citations[0]['source'] == 'Google'
            assert citations[0]['url'] == 'https://www.google.com'
            assert citations[1]['source'] == 'GitHub'
            assert citations[1]['url'] == 'https://github.com'
        finally:
            os.unlink(temp_path)

    def test_bare_urls(self):
        """Test extraction of bare URLs."""
        content = """
        Visit https://example.com for more info.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            citations = extract_citations(temp_path)
            assert len(citations) == 1
            assert citations[0]['source'] == 'Bare URL'
            assert citations[0]['url'] == 'https://example.com'
        finally:
            os.unlink(temp_path)

    def test_doi_references(self):
        """Test extraction of DOI references."""
        content = """
        See DOI: 10.1038/s41586-020-2649-2 for details.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            citations = extract_citations(temp_path)
            assert len(citations) == 1
            assert citations[0]['source'] == 'DOI'
            assert '10.1038/s41586-020-2649-2' in citations[0]['original_doi']
            assert 'https://doi.org/' in citations[0]['url']
        finally:
            os.unlink(temp_path)

class TestVerifyCitation:
    @patch('verify_citations.requests.head')
    def test_reachable_url(self, mock_head):
        """Test verification of a reachable URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        result = verify_citation('https://example.com')
        assert result['status'] == 'reachable'
        assert result['response_code'] == 200

    @patch('verify_citations.requests.head')
    def test_unreachable_url(self, mock_head):
        """Test verification of an unreachable URL."""
        mock_head.side_effect = Exception("Connection failed")

        result = verify_citation('https://invalid-url-12345.com')
        assert result['status'] == 'unreachable'

    @patch('verify_citations.requests.head')
    def test_mismatch_status(self, mock_head):
        """Test verification of a URL returning non-200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        result = verify_citation('https://example.com/not-found')
        assert result['status'] == 'mismatch'
        assert result['response_code'] == 404

class TestFindArtifacts:
    def test_find_markdown_files(self):
        """Test finding markdown files in a directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create some test files
            (tmpdir_path / 'README.md').touch()
            (tmpdir_path / 'docs').mkdir()
            (tmpdir_path / 'docs' / 'guide.md').touch()
            (tmpdir_path / 'other.txt').touch()

            artifacts = find_artifacts(tmpdir_path, ['*.md', 'docs/*.md'])
            assert len(artifacts) == 2
            assert any('README.md' in str(a) for a in artifacts)
            assert any('guide.md' in str(a) for a in artifacts)

class TestVerifyAllCitations:
    def test_full_verification_flow(self):
        """Test the full citation verification flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a test artifact
            artifact = tmpdir_path / 'test.md'
            artifact.write_text("Check [Example](https://example.com)")
            
            state_dir = tmpdir_path / 'state'
            state_dir.mkdir()
            output_path = state_dir / 'citation_log.yaml'

            results = verify_all_citations(
                project_root=tmpdir_path,
                patterns=['*.md'],
                output_path=output_path
            )

            assert output_path.exists()
            assert results['summary']['total_citations'] == 1
            
            # Verify the YAML file structure
            with open(output_path, 'r') as f:
                loaded = yaml.safe_load(f)
                assert 'citations' in loaded
                assert 'summary' in loaded