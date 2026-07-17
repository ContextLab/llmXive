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
    create_code_snippets,
    save_snippets_to_csv
)
from src.models.code_snippet import CodeSnippet, create_snippet

class TestNormalizeLabel:
    def test_vulnerable_variants(self):
        """Test various vulnerable label variants normalize correctly."""
        variants = ["vulnerable", "VULNERABLE", "vuln", "1", "true", "yes", "positive"]
        for variant in variants:
            assert normalize_label(variant) == "vulnerable"

    def test_safe_variants(self):
        """Test various safe label variants normalize correctly."""
        variants = ["safe", "SAFE", "non-vulnerable", "0", "false", "no", "negative", "benign"]
        for variant in variants:
            assert normalize_label(variant) == "safe"

    def test_unknown_variants(self):
        """Test unknown label variants."""
        variants = ["unknown", "UNKN", "null", "", None]
        for variant in variants:
            assert normalize_label(variant) == "unknown"

class TestDetectLanguage:
    def test_common_extensions(self):
        """Test detection of common programming language extensions."""
        assert detect_language_from_extension("test.py") == "python"
        assert detect_language_from_extension("test.c") == "c"
        assert detect_language_from_extension("test.cpp") == "cpp"
        assert detect_language_from_extension("test.java") == "java"
        assert detect_language_from_extension("test.js") == "javascript"
        assert detect_language_from_extension("test.go") == "go"

    def test_unknown_extension(self):
        """Test detection of unknown extension."""
        assert detect_language_from_extension("test.xyz") == "unknown"

class TestExtractCategory:
    def test_sql_injection(self):
        """Test SQL injection category extraction."""
        assert extract_category_from_context("SQL injection vulnerability") == "sql_injection"
        assert extract_category_from_context("SQLi vulnerability") == "sql_injection"

    def test_buffer_overflow(self):
        """Test buffer overflow category extraction."""
        assert extract_category_from_context("buffer overflow issue") == "buffer_overflow"
        assert extract_category_from_context("memory overflow") == "overflow"

    def test_unknown_category(self):
        """Test unknown category returns 'unknown'."""
        assert extract_category_from_context("some random text") == "unknown"
        assert extract_category_from_context(None) == "unknown"

class TestParseVulDeePecker:
    def test_parse_valid_jsonl(self):
        """Test parsing a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({
                "id": "test_001",
                "code": "int x = 0;",
                "label": "vulnerable",
                "language": "c",
                "category": "overflow",
                "context": "integer overflow"
            }) + "\n")
            f.write(json.dumps({
                "id": "test_002",
                "code": "safe code here",
                "label": "safe",
                "language": "c"
            }) + "\n")
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            assert len(snippets) == 2
            assert snippets[0]["id"] == "test_001"
            assert snippets[0]["label"] == "vulnerable"
            assert snippets[1]["label"] == "safe"
        finally:
            os.unlink(temp_path)

    def test_parse_empty_lines(self):
        """Test that empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write("\n")
            f.write(json.dumps({"id": "test", "code": "x=1", "label": "safe"}) + "\n")
            f.write("\n")
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            assert len(snippets) == 1
        finally:
            os.unlink(temp_path)

    def test_parse_malformed_json(self):
        """Test that malformed JSON lines are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write("not valid json\n")
            f.write(json.dumps({"id": "test", "code": "x=1", "label": "safe"}) + "\n")
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            assert len(snippets) == 1
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        """Test handling of missing file."""
        snippets = parse_vuldeepecker_jsonl(Path("/nonexistent/file.jsonl"))
        assert len(snippets) == 0

class TestParseJuliet:
    def test_parse_c_test_cases(self):
        """Test parsing Juliet C test case structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Juliet structure
            test_case_dir = Path(tmpdir) / "CWE126_Buffer_Overflow"
            test_case_dir.mkdir()
            bad_dir = test_case_dir / "CWE126_Buffer_Overflow_bad"
            bad_dir.mkdir()
            good_dir = test_case_dir / "CWE126_Buffer_Overflow_good"
            good_dir.mkdir()

            # Create test files
            bad_file = bad_dir / "test.c"
            bad_file.write_text("void vulnerable() { /* bad code */ }")
            good_file = good_dir / "test.c"
            good_file.write_text("void safe() { /* good code */ }")

            snippets = parse_juliet_c_test_cases(Path(tmpdir))

            assert len(snippets) == 2
            vulnerable_snippets = [s for s in snippets if s["label"] == "vulnerable"]
            safe_snippets = [s for s in snippets if s["label"] == "safe"]
            assert len(vulnerable_snippets) == 1
            assert len(safe_snippets) == 1

    def test_parse_java_test_cases(self):
        """Test parsing Juliet Java test case structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_case_dir = Path(tmpdir) / "CWE89_SQL_Injection"
            test_case_dir.mkdir()
            bad_dir = test_case_dir / "CWE89_SQL_Injection_bad"
            bad_dir.mkdir()
            good_dir = test_case_dir / "CWE89_SQL_Injection_good"
            good_dir.mkdir()

            bad_file = bad_dir / "Test.java"
            bad_file.write_text("public class Test { /* bad */ }")
            good_file = good_dir / "Test.java"
            good_file.write_text("public class Safe { /* good */ }")

            from src.data.preprocess import parse_juliet_java_test_cases
            snippets = parse_juliet_java_test_cases(Path(tmpdir))

            assert len(snippets) == 2

class TestCreateCodeSnippets:
    def test_create_from_valid_snippets(self):
        """Test creating CodeSnippet entities from valid raw snippets."""
        raw_snippets = [
            {
                "id": "test_001",
                "code": "int x = 0;",
                "label": "vulnerable",
                "language": "c",
                "category": "overflow"
            },
            {
                "id": "test_002",
                "code": "safe code",
                "label": "safe",
                "language": "c"
            }
        ]

        snippets = create_code_snippets(raw_snippets)

        assert len(snippets) == 2
        assert all(isinstance(s, CodeSnippet) for s in snippets)
        assert snippets[0].ground_truth_label == "vulnerable"
        assert snippets[1].ground_truth_label == "safe"

    def test_excludes_unknown_labels(self):
        """Test that snippets with unknown labels are excluded."""
        raw_snippets = [
            {"id": "test_001", "code": "x=1", "label": "vulnerable", "language": "c"},
            {"id": "test_002", "code": "y=2", "label": "unknown", "language": "c"},
            {"id": "test_003", "code": "z=3", "label": None, "language": "c"},
            {"id": "test_004", "code": "w=4", "label": "", "language": "c"}
        ]

        snippets = create_code_snippets(raw_snippets)

        assert len(snippets) == 1
        assert snippets[0].id == "test_001"

    def test_normalizes_labels(self):
        """Test that labels are properly normalized."""
        raw_snippets = [
            {"id": "test_001", "code": "x=1", "label": "VULNERABLE", "language": "c"},
            {"id": "test_002", "code": "y=2", "label": "SAFE", "language": "c"},
            {"id": "test_003", "code": "z=3", "label": "1", "language": "c"},
            {"id": "test_004", "code": "w=4", "label": "0", "language": "c"}
        ]

        snippets = create_code_snippets(raw_snippets)

        assert snippets[0].ground_truth_label == "vulnerable"
        assert snippets[1].ground_truth_label == "safe"
        assert snippets[2].ground_truth_label == "vulnerable"
        assert snippets[3].ground_truth_label == "safe"

class TestSaveSnippetsToCSV:
    def test_save_and_load(self):
        """Test saving snippets to CSV and verifying content."""
        snippets = [
            create_snippet("test_001", "python", "x=1", "vulnerable", "input_validation"),
            create_snippet("test_002", "python", "y=2", "safe", "input_validation")
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)

        try:
            save_snippets_to_csv(snippets, temp_path)

            assert temp_path.exists()
            with open(temp_path, 'r') as csv_file:
                content = csv_file.read()
                assert "test_001" in content
                assert "test_002" in content
                assert "vulnerable" in content
                assert "safe" in content
        finally:
            os.unlink(temp_path)