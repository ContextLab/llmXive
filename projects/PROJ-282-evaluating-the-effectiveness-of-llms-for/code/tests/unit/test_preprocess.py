"""
Unit tests for the preprocessing module.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.preprocess import (
    detect_language_from_extension,
    normalize_label,
    extract_category_from_context,
    parse_vuldeepecker_jsonl,
    parse_juliet_c_test_cases,
    parse_juliet_java_test_cases,
    parse_raw_directory,
    create_code_snippets,
    save_snippets_to_csv,
    log_edge_cases,
)
from src.models.code_snippet import CodeSnippet, create_snippet


class TestNormalizeLabel:
    def test_normalize_sql_injection(self):
        assert normalize_label("sql injection") == "SQLi"
        assert normalize_label("SQLi") == "SQLi"
        assert normalize_label("injection") == "SQLi"

    def test_normalize_buffer_overflow(self):
        assert normalize_label("buffer overflow") == "Buffer Overflow"
        assert normalize_label("overflow") == "Buffer Overflow"

    def test_normalize_none(self):
        assert normalize_label("none") == "none"
        assert normalize_label("safe") == "none"
        assert normalize_label("no vulnerability") == "none"

    def test_normalize_unknown(self):
        assert normalize_label("unknown_type") == "unknown_type"

    def test_normalize_empty(self):
        assert normalize_label("") is None
        assert normalize_label(None) is None


class TestDetectLanguage:
    def test_python(self):
        assert detect_language_from_extension("file.py") == "Python"

    def test_c(self):
        assert detect_language_from_extension("file.c") == "C"

    def test_cpp(self):
        assert detect_language_from_extension("file.cpp") == "C++"
        assert detect_language_from_extension("file.cc") == "C++"

    def test_java(self):
        assert detect_language_from_extension("file.java") == "Java"

    def test_unknown(self):
        assert detect_language_from_extension("file.xyz") is None


class TestExtractCategory:
    def test_extract_sql(self):
        assert extract_category_from_context("This code has a SQL injection vulnerability") == "SQLi"

    def test_extract_overflow(self):
        assert extract_category_from_context("Buffer overflow detected") == "Buffer Overflow"

    def test_extract_none(self):
        assert extract_category_from_context("No issues found") is None

    def test_extract_empty(self):
        assert extract_category_from_context("") is None


class TestParseVulDeePecker:
    @pytest.fixture
    def temp_jsonl_file(self, tmp_path):
        jsonl_path = tmp_path / "test.jsonl"
        data = [
            {"id": "1", "language": "Python", "code": "x = 1", "label": "safe"},
            {"id": "2", "language": "Python", "code": "exec(input())", "label": "sql injection"},
        ]
        with open(jsonl_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        return jsonl_path

    def test_parse_jsonl(self, temp_jsonl_file):
        snippets = parse_vuldeepecker_jsonl(temp_jsonl_file)
        assert len(snippets) == 2
        assert snippets[0]["source_id"] == "1"
        assert snippets[0]["language"] == "Python"
        assert snippets[0]["ground_truth_label"] == "safe"
        assert snippets[1]["ground_truth_label"] == "sql injection"


class TestParseJuliet:
    @pytest.fixture
    def temp_juliet_c_dir(self, tmp_path):
        cwe_dir = tmp_path / "cwe-89"
        cwe_dir.mkdir()
        
        bad_file = cwe_dir / "bad.c"
        bad_file.write_text("int main() { return 0; }")
        
        good_file = cwe_dir / "good.c"
        good_file.write_text("int main() { return 1; }")
        
        return tmp_path

    def test_parse_c_test_cases(self, temp_juliet_c_dir):
        snippets = parse_juliet_c_test_cases(temp_juliet_c_dir)
        assert len(snippets) == 2
        
        bad_snippet = next(s for s in snippets if "bad.c" in s["source_id"])
        assert bad_snippet["ground_truth_label"] == "vulnerable"
        assert bad_snippet["language"] == "C"
        
        good_snippet = next(s for s in snippets if "good.c" in s["source_id"])
        assert good_snippet["ground_truth_label"] == "none"


class TestCreateCodeSnippets:
    def test_create_snippets_valid(self):
        raw_data = [
            {
                "source_id": "1",
                "language": "Python",
                "source_code": "x = 1",
                "ground_truth_label": "safe",
                "ground_truth_category": None,
            }
        ]
        
        snippets, edge_cases = create_code_snippets(raw_data)
        
        assert len(snippets) == 1
        assert len(edge_cases) == 0
        assert snippets[0].snippet_id == "1"
        assert snippets[0].ground_truth_label == "none"

    def test_create_snippets_missing_label(self):
        raw_data = [
            {
                "source_id": "2",
                "language": "C",
                "source_code": "int main() {}",
                "ground_truth_label": None,
                "ground_truth_category": None,
            }
        ]
        
        snippets, edge_cases = create_code_snippets(raw_data)
        
        assert len(snippets) == 1
        assert len(edge_cases) == 1
        assert snippets[0].label_missing is True
        assert edge_cases[0]["reason"] == "missing_ground_truth_label"


class TestSaveSnippetsToCSV:
    @pytest.fixture
    def temp_csv_file(self, tmp_path):
        return tmp_path / "test.csv"

    def test_save_valid_snippets(self, temp_csv_file):
        snippets = [
            create_snippet(
                snippet_id="1",
                language="Python",
                source_code="x = 1",
                ground_truth_label="none",
            ),
            create_snippet(
                snippet_id="2",
                language="C",
                source_code="int main() {}",
                ground_truth_label="vulnerable",
            ),
        ]
        
        save_snippets_to_csv(snippets, temp_csv_file, include_missing=False)
        
        assert temp_csv_file.exists()
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["snippet_id"] == "1"
            assert rows[1]["snippet_id"] == "2"

    def test_save_with_missing_labels(self, temp_csv_file):
        snippets = [
            create_snippet(
                snippet_id="1",
                language="Python",
                source_code="x = 1",
                ground_truth_label="none",
            ),
            create_snippet(
                snippet_id="2",
                language="C",
                source_code="int main() {}",
                ground_truth_label=None,
            ),
        ]
        # Manually set label_missing for testing
        snippets[1].label_missing = True
        
        save_snippets_to_csv(snippets, temp_csv_file, include_missing=True)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[1]["label_missing"] == "True"
        
        # Test exclude missing
        save_snippets_to_csv(snippets, temp_csv_file, include_missing=False)
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1


class TestLogEdgeCases:
    @pytest.fixture
    def temp_log_file(self, tmp_path):
        return tmp_path / "edge_cases.json"

    def test_log_edge_cases(self, temp_log_file):
        edge_cases = [
            {"snippet_id": "1", "reason": "missing_label"},
            {"snippet_id": "2", "reason": "invalid_format"},
        ]
        
        log_edge_cases(edge_cases, temp_log_file)
        
        assert temp_log_file.exists()
        with open(temp_log_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[0]["snippet_id"] == "1"


import csv