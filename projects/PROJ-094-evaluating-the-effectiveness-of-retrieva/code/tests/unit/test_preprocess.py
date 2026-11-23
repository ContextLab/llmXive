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
    load_and_process_subset,
    save_to_jsonl,
    save_to_csv
)
from src.data.models import CodeSnippet

class TestStripNonAscii:
    def test_clean_ascii(self):
        text = "Hello World"
        assert strip_non_ascii(text) == "Hello World"

    def test_mixed_ascii_unicode(self):
        text = "Hello Wörld"
        expected = "Hello Wrl" # 'ö' is non-ascii, removed
        # Note: 'ö' (U+00F6) is non-ASCII.
        # The function removes it.
        result = strip_non_ascii(text)
        assert 'ö' not in result

    def test_empty_string(self):
        assert strip_non_ascii("") == ""

    def test_none_input(self):
        assert strip_non_ascii(None) == ""

class TestTokenizeAndTruncate:
    def test_no_truncation(self):
        text = "one two three"
        result = tokenize_and_truncate(text, max_tokens=5)
        assert result == "one two three"

    def test_truncation(self):
        text = "one two three four five six"
        result = tokenize_and_truncate(text, max_tokens=3)
        assert result == "one two three"

    def test_empty_string(self):
        assert tokenize_and_truncate("", max_tokens=5) == ""

    def test_single_token(self):
        text = "hello"
        result = tokenize_and_truncate(text, max_tokens=1)
        assert result == "hello"

class TestProcessSnippet:
    def test_process_valid_item(self):
        raw_item = {
            'code': 'def foo(): pass',
            'language': 'python',
            'docstring': 'A function.',
            'repo': 'test/repo',
            'function_name': 'foo',
            'id': '123'
        }
        snippet = process_snippet(raw_item)
        assert snippet.code == "def foo(): pass"
        assert snippet.language == "python"
        assert snippet.docstring == "A function."
        assert snippet.repo == "test/repo"
        assert snippet.function_name == "foo"
        assert snippet.raw_id == "123"

    def test_process_truncation(self):
        long_code = " ".join(["word"] * 300)
        raw_item = {
            'code': long_code,
            'language': 'python',
            'docstring': 'Short',
            'repo': 'test/repo',
            'function_name': 'foo',
            'id': '123'
        }
        snippet = process_snippet(raw_item)
        # Should be truncated to 256 tokens
        tokens = snippet.code.split()
        assert len(tokens) <= 256

class TestSaveToJsonl:
    def test_save_single_snippet(self):
        snippet = CodeSnippet(
            code="x = 1",
            language="python",
            docstring="doc",
            repo="r",
            function_name="f",
            raw_id="1"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            save_to_jsonl([snippet], str(path))
            assert path.exists()
            with open(path, 'r') as f:
                line = f.readline()
                data = json.loads(line)
                assert data['code'] == "x = 1"

    def test_save_multiple_snippets(self):
        snippets = [
            CodeSnippet("c1", "py", "d1", "r1", "f1", "1"),
            CodeSnippet("c2", "py", "d2", "r2", "f2", "2")
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            save_to_jsonl(snippets, str(path))
            assert path.exists()
            with open(path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2

class TestSaveToCsv:
    def test_save_single_snippet(self):
        snippet = CodeSnippet(
            code="x = 1",
            language="python",
            docstring="doc",
            repo="r",
            function_name="f",
            raw_id="1"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.csv"
            save_to_csv([snippet], str(path))
            assert path.exists()
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['code'] == "x = 1"

    def test_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.csv"
            # Should not raise, just log warning
            save_to_csv([], str(path))
            # File might not be created or be empty depending on implementation
            # The function handles empty list by logging warning and returning
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                    # Should only have header if created, or be empty
                    pass