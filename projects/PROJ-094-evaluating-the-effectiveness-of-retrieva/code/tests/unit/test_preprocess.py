"""
Unit tests for the preprocessing module.
"""
import pytest
import tempfile
import json
import csv
from pathlib import Path

from src.data.preprocess import (
    strip_non_ascii,
    tokenize_and_truncate,
    process_snippet,
    save_to_jsonl,
    save_to_csv
)
from src.data.models import CodeSnippet


class TestStripNonAscii:
    """Tests for the strip_non_ascii function."""

    def test_ascii_only(self):
        """Test that ASCII-only text is unchanged."""
        text = "Hello, world! 123"
        assert strip_non_ascii(text) == text

    def test_non_ascii_removal(self):
        """Test that non-ASCII characters are removed."""
        text = "Hello, 世界! 🌍"
        expected = "Hello, ! "
        assert strip_non_ascii(text) == expected

    def test_empty_string(self):
        """Test handling of empty string."""
        assert strip_non_ascii("") == ""

    def test_none_input(self):
        """Test handling of None input."""
        assert strip_non_ascii(None) == ""

    def test_non_string_input(self):
        """Test handling of non-string input."""
        assert strip_non_ascii(123) == "123"


class TestTokenizeAndTruncate:
    """Tests for the tokenize_and_truncate function."""

    def test_no_truncation_needed(self):
        """Test that text shorter than max_tokens is unchanged."""
        text = "Hello world this is a test"
        assert tokenize_and_truncate(text, max_tokens=10) == text

    def test_truncation(self):
        """Test that text is truncated to max_tokens."""
        text = " ".join(["word"] * 100)
        result = tokenize_and_truncate(text, max_tokens=10)
        tokens = result.split()
        assert len(tokens) == 10

    def test_empty_string(self):
        """Test handling of empty string."""
        assert tokenize_and_truncate("") == ""

    def test_none_input(self):
        """Test handling of None input."""
        assert tokenize_and_truncate(None) == ""


class TestProcessSnippet:
    """Tests for the process_snippet function."""

    def test_basic_processing(self):
        """Test basic snippet processing."""
        raw = {
            'code': "def hello():\n    print('Hello')",
            'language': 'python',
            'repo': 'test/repo',
            'path': 'hello.py',
            'commit_hash': 'abc123'
        }
        snippet = process_snippet(raw)

        assert isinstance(snippet, CodeSnippet)
        assert snippet.language == 'python'
        assert snippet.repo == 'test/repo'
        assert snippet.path == 'hello.py'
        assert snippet.commit_hash == 'abc123'
        assert len(snippet.code) > 0

    def test_non_ascii_removal_in_code(self):
        """Test that non-ASCII is removed from code."""
        raw = {
            'code': "def hello():\n    print('你好')",
            'language': 'python',
            'repo': 'test/repo',
            'path': 'hello.py',
            'commit_hash': 'abc123'
        }
        snippet = process_snippet(raw)
        assert '你' not in snippet.code
        assert '好' not in snippet.code

    def test_missing_fields(self):
        """Test handling of missing fields."""
        raw = {'code': 'print("test")'}
        snippet = process_snippet(raw)

        assert snippet.language == 'unknown'
        assert snippet.repo == 'unknown'
        assert snippet.path == 'unknown'
        assert snippet.commit_hash == 'unknown'


class TestSaveToJsonl:
    """Tests for the save_to_jsonl function."""

    def test_save_and_load(self):
        """Test saving snippets to JSONL and reading back."""
        snippets = [
            CodeSnippet(
                code="print('test')",
                language='python',
                repo='test/repo',
                path='test.py',
                commit_hash='abc123',
                original_length=3,
                processed_length=3
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.jsonl'
            save_to_jsonl(snippets, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                line = f.readline()
                data = json.loads(line)

            assert data['code'] == "print('test')"
            assert data['language'] == 'python'


class TestSaveToCsv:
    """Tests for the save_to_csv function."""

    def test_save_and_load(self):
        """Test saving snippets to CSV and reading back."""
        snippets = [
            CodeSnippet(
                code="print('test')",
                language='python',
                repo='test/repo',
                path='test.py',
                commit_hash='abc123',
                original_length=3,
                processed_length=3
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.csv'
            save_to_csv(snippets, output_path)

            assert output_path.exists()

            with open(output_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                row = next(reader)

            assert row['code'] == "print('test')"
            assert row['language'] == 'python'
            assert row['original_length'] == '3'