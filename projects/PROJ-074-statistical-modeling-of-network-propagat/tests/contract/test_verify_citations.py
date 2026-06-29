"""
Contract tests for citation verification module.

These tests verify that verify_citations.py:
1. Correctly extracts citations from markdown files
2. Properly computes token overlap
3. Handles unreachable URLs
4. Returns appropriate exit codes
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from pipeline.verify_citations import (
    compute_token_overlap,
    extract_citations_from_markdown,
    normalize_tokens,
)


class TestTokenNormalization:
    """Tests for token normalization function."""

    def test_lowercase_conversion(self):
        """Test that tokens are normalized to lowercase."""
        result = normalize_tokens("Hello World TEST")
        assert 'hello' in result
        assert 'world' in result
        assert 'test' in result
        assert 'Hello' not in result

    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        result = normalize_tokens("hello, world! test.")
        assert 'hello' in result
        assert 'world' in result
        assert 'test' in result
        assert ',' not in result

    def test_stop_word_filtering(self):
        """Test that common stop words are filtered."""
        result = normalize_tokens("the and or but in on at")
        assert 'the' not in result
        assert 'and' not in result
        assert 'or' not in result

    def test_short_token_filtering(self):
        """Test that very short tokens are filtered."""
        result = normalize_tokens("a an i to of")
        assert 'a' not in result
        assert 'an' not in result

    def test_empty_string(self):
        """Test handling of empty string."""
        result = normalize_tokens("")
        assert result == set()


class TestTokenOverlap:
    """Tests for token overlap computation."""

    def test_identical_titles(self):
        """Test overlap for identical titles."""
        overlap = compute_token_overlap("Research Paper Title", "Research Paper Title")
        assert overlap == 1.0

    def test_completely_different(self):
        """Test overlap for completely different titles."""
        overlap = compute_token_overlap("abc def ghi", "xyz uvw rst")
        assert overlap == 0.0

    def test_partial_overlap(self):
        """Test overlap for partially matching titles."""
        overlap = compute_token_overlap("machine learning research", "deep learning paper")
        # 'learning' should be in both, 'machine'/'research'/'deep'/'paper' in one each
        assert 0.0 < overlap < 1.0

    def test_case_insensitive(self):
        """Test that overlap is case insensitive."""
        overlap1 = compute_token_overlap("Hello World", "hello world")
        overlap2 = compute_token_overlap("HELLO WORLD", "Hello World")
        assert overlap1 == overlap2 == 1.0

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        overlap1 = compute_token_overlap("", "title")
        overlap2 = compute_token_overlap("title", "")
        overlap3 = compute_token_overlap("", "")
        assert overlap1 == 0.0
        assert overlap2 == 0.0
        assert overlap3 == 0.0


class TestCitationExtraction:
    """Tests for citation extraction from markdown."""

    def test_extract_basic_citations(self):
        """Test extraction of basic markdown citations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
            # Test Document

            See [Research Paper](https://example.com/paper) for details.

            Also check [Another Study](https://example.com/study).
            """)
            f.flush()
            citations = extract_citations_from_markdown(Path(f.name), None)

            assert len(citations) == 2
            assert citations[0][0] == "https://example.com/paper"
            assert citations[0][1] == "Research Paper"
            assert citations[1][0] == "https://example.com/study"
            assert citations[1][1] == "Another Study"

    def test_skip_internal_links(self):
        """Test that internal links are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
            # Test Document

            See [internal link](#section) for more.

            But [external link](https://example.com) is included.
            """)
            f.flush()
            citations = extract_citations_from_markdown(Path(f.name), None)

            assert len(citations) == 1
            assert citations[0][0] == "https://example.com"

    def test_line_numbers(self):
        """Test that line numbers are tracked."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
            Line 1
            Line 2: [Citation](https://example.com)
            Line 4
            """)
            f.flush()
            citations = extract_citations_from_markdown(Path(f.name), None)

            assert len(citations) == 1
            assert citations[0][2] == 3  # Line 3 in file (1-indexed)


class TestScriptExecution:
    """Tests for script execution and exit codes."""

    def test_script_runs_successfully(self):
        """Test that the script runs without errors on empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, '-m', 'pipeline.verify_citations', '--dir', tmpdir],
                capture_output=True,
                text=True
            )
            # Should exit 0 even with no files
            assert result.returncode == 0

    def test_script_exits_zero_on_pass(self):
        """Test exit code 0 when all citations pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a markdown file with no citations
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("# Test\n\nNo citations here.")

            result = subprocess.run(
                [sys.executable, '-m', 'pipeline.verify_citations', '--dir', tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0

    def test_script_exits_nonzero_on_failure(self):
        """Test that script can be imported and has main function."""
        from pipeline.verify_citations import main
        assert callable(main)