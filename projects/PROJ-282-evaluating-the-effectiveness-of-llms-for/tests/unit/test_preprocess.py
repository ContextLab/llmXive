import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.data.preprocess import (
    detect_language_from_extension, normalize_label, extract_category_from_context,
    parse_vuldeepecker_jsonl, parse_juliet_c_test_cases, parse_juliet_java_test_cases,
    parse_raw_directory, create_code_snippets, save_snippets_to_csv, log_edge_cases, main
)


class TestNormalizeLabel:
    def test_normalize_sql_injection(self):
        assert normalize_label("SQL Injection") == "SQLi"
        assert normalize_label("sqli") == "SQLi"

    def test_normalize_buffer_overflow(self):
        assert normalize_label("Buffer Overflow") == "Buffer Overflow"
        assert normalize_label("overflow") == "Buffer Overflow"

    def test_normalize_none(self):
        assert normalize_label("No vulnerability") == "none"
        assert normalize_label("Safe") == "none"

class TestDetectLanguage:
    def test_py_extension(self):
        assert detect_language_from_extension("file.py") == "Python"
        assert detect_language_from_extension("FILE.PY") == "Python"

    def test_c_extension(self):
        assert detect_language_from_extension("file.c") == "C"
        assert detect_language_from_extension("file.cpp") == "C++"

    def test_unknown_extension(self):
        assert detect_language_from_extension("file.xyz") == "Unknown"

class TestExtractCategory:
    def test_context_contains_injection(self):
        assert extract_category_from_context("This function handles SQL injection") == "SQLi"

    def test_no_category_found(self):
        assert extract_category_from_context("General code snippet") == "Unknown"

class TestParseVulDeePecker:
    def test_parse_jsonl(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"code": "print(1)", "label": "Safe"}\n')
            f.flush()
            snippets = parse_vuldeepecker_jsonl(Path(f.name))
            assert len(snippets) == 1
            assert snippets[0].code == "print(1)"
        os.unlink(f.name)

class TestParseJuliet:
    def test_parse_c_test_case(self):
        # Mock file content
        with patch('builtins.open', mock_open(read_data="int main() { return 0; }")):
            # This is a simplified test; real implementation parses C test cases
            pass

class TestCreateCodeSnippets:
    def test_create_from_raw(self):
        raw_data = [{"code": "x=1", "label": "Safe", "file": "test.py"}]
        snippets = create_code_snippets(raw_data, source="test")
        assert len(snippets) == 1
        assert snippets[0].code == "x=1"

class TestSaveSnippetsToCSV:
    def test_save_to_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "snippets.csv"
            # Create dummy snippets
            from src.models.code_snippet import create_snippet
            snippets = [create_snippet("code", "py", "src")]
            save_snippets_to_csv(snippets, output_path)
            assert output_path.exists()

class TestLogEdgeCases:
    def test_log_missing_label(self, caplog):
        from src.utils.logger import get_logger
        logger = get_logger("test")
        log_edge_cases(logger, [{"code": "x", "label": None}])
        # Check that a warning was logged
        assert any("missing label" in str(record).lower() for record in caplog.records)
