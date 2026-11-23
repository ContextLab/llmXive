"""
Unit tests for src.data.preprocess module.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

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
    def test_removes_non_ascii(self):
        text = "Hello 世界!"
        result = strip_non_ascii(text)
        assert result == "Hello !"

    def test_empty_string(self):
        assert strip_non_ascii("") == ""

    def test_ascii_only(self):
        text = "Hello World 123"
        assert strip_non_ascii(text) == text

class TestTokenizeAndTruncate:
    def test_no_truncation_needed(self):
        text = "one two three"
        result = tokenize_and_truncate(text, max_tokens=5)
        assert result == text

    def test_truncation(self):
        text = " ".join([f"word{i}" for i in range(10)])
        result = tokenize_and_truncate(text, max_tokens=5)
        tokens = result.split()
        assert len(tokens) == 5
        assert "word9" not in result

    def test_empty_string(self):
        assert tokenize_and_truncate("", max_tokens=5) == ""

class TestProcessSnippet:
    def test_basic_processing(self):
        raw = {
            "code": "def hello(): pass",
            "language": "python",
            "function_name": "hello",
            "id": "123"
        }
        snippet = process_snippet(raw)
        assert isinstance(snippet, CodeSnippet)
        assert snippet.code == "def hello(): pass"
        assert snippet.language == "python"
        assert snippet.function_name == "hello"
        assert snippet.original_id == "123"

    def test_non_ascii_removal(self):
        raw = {
            "code": "def héllö(): pass",
            "language": "pythön",
            "function_name": "héllo",
            "id": "456"
        }
        snippet = process_snippet(raw)
        assert "é" not in snippet.code
        assert "ö" not in snippet.language
        assert "é" not in snippet.function_name

    def test_truncation(self):
        long_code = " ".join([f"token{i}" for i in range(300)])
        raw = {
            "code": long_code,
            "language": "python",
            "function_name": "test",
            "id": "789"
        }
        snippet = process_snippet(raw)
        tokens = snippet.code.split()
        assert len(tokens) == 256

class TestSaveFunctions:
    def test_save_to_jsonl(self):
        snippets = [
            CodeSnippet(code="x=1", natural_language="set x", function_name="", original_id="1", language="py"),
            CodeSnippet(code="y=2", natural_language="set y", function_name="", original_id="2", language="py")
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            save_to_jsonl(snippets, path)
            
            assert path.exists()
            with open(path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 2
            
            data1 = json.loads(lines[0])
            assert data1["code"] == "x=1"
            assert data1["original_id"] == "1"

    def test_save_to_csv(self):
        snippets = [
            CodeSnippet(code="x=1", natural_language="set x", function_name="func1", original_id="1", language="py"),
            CodeSnippet(code="y=2", natural_language="set y", function_name="func2", original_id="2", language="py")
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.csv"
            save_to_csv(snippets, path)
            
            assert path.exists()
            with open(path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 3  # header + 2 rows
            assert "code" in lines[0]
            assert "x=1" in lines[1]