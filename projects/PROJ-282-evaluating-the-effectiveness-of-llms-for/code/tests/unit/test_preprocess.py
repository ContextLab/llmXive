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
    create_code_snippets,
    save_snippets_to_csv,
    log_edge_cases,
)
from src.models.code_snippet import CodeSnippet

class TestNormalizeLabel:
    def test_normalize_vulnerable_labels(self):
        """Test normalization of vulnerable labels."""
        assert normalize_label('vulnerable') == 'vulnerable'
        assert normalize_label('vuln') == 'vulnerable'
        assert normalize_label('unsafe') == 'vulnerable'
        assert normalize_label('1') == 'vulnerable'
        assert normalize_label('true') == 'vulnerable'
        assert normalize_label('yes') == 'vulnerable'
        assert normalize_label('bad') == 'vulnerable'

    def test_normalize_safe_labels(self):
        """Test normalization of safe labels."""
        assert normalize_label('safe') == 'safe'
        assert normalize_label('secure') == 'safe'
        assert normalize_label('benign') == 'safe'
        assert normalize_label('0') == 'safe'
        assert normalize_label('false') == 'safe'
        assert normalize_label('no') == 'safe'
        assert normalize_label('clean') == 'safe'

    def test_normalize_case_insensitive(self):
        """Test that normalization is case-insensitive."""
        assert normalize_label('VULNERABLE') == 'vulnerable'
        assert normalize_label('Safe') == 'safe'
        assert normalize_label('Vuln') == 'vulnerable'

    def test_normalize_none_input(self):
        """Test that None input returns None."""
        assert normalize_label(None) is None
        assert normalize_label('') is None
        assert normalize_label('   ') is None

    def test_normalize_unknown_label(self):
        """Test that unknown labels return None."""
        assert normalize_label('unknown') is None
        assert normalize_label('maybe') is None

class TestDetectLanguage:
    def test_detect_python(self):
        """Test Python language detection."""
        assert detect_language_from_extension('file.py') == 'Python'
        assert detect_language_from_extension('/path/to/file.py') == 'Python'

    def test_detect_c(self):
        """Test C language detection."""
        assert detect_language_from_extension('file.c') == 'C'
        assert detect_language_from_extension('file.cpp') == 'C++'
        assert detect_language_from_extension('file.cc') == 'C++'

    def test_detect_java(self):
        """Test Java language detection."""
        assert detect_language_from_extension('file.java') == 'Java'

    def test_detect_javascript(self):
        """Test JavaScript language detection."""
        assert detect_language_from_extension('file.js') == 'JavaScript'

    def test_detect_unknown_extension(self):
        """Test unknown extension returns None."""
        assert detect_language_from_extension('file.xyz') is None
        assert detect_language_from_extension('file') is None

class TestExtractCategory:
    def test_extract_sql_injection(self):
        """Test SQL injection category extraction."""
        assert extract_category_from_context("SELECT * FROM users WHERE id = " + "1") == 'sql_injection'
        assert extract_category_from_context("", "CWE-89") == 'sql_injection'

    def test_extract_buffer_overflow(self):
        """Test buffer overflow category extraction."""
        assert extract_category_from_context("strcpy(dest, src)") == 'buffer_overflow'
        assert extract_category_from_context("", "CWE-120") == 'buffer_overflow'

    def test_extract_xss(self):
        """Test XSS category extraction."""
        assert extract_category_from_context("<script>alert('xss')</script>") == 'xss'

    def test_no_category_found(self):
        """Test when no category is found."""
        assert extract_category_from_context("normal code") is None

class TestParseVulDeePecker:
    def test_parse_valid_jsonl(self):
        """Test parsing valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump({'code': 'print("hello")', 'label': 'vulnerable', 'language': 'Python'}, f)
            f.write('\n')
            json.dump({'code': 'print("world")', 'label': 'safe', 'language': 'Python'}, f)
            f.write('\n')
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            assert len(snippets) == 2
            assert snippets[0]['label'] == 'vulnerable'
            assert snippets[1]['label'] == 'safe'
            assert snippets[0]['language'] == 'Python'
        finally:
            os.unlink(temp_path)

    def test_parse_empty_file(self):
        """Test parsing empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            assert len(snippets) == 0
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        snippets = parse_vuldeepecker_jsonl(Path('/nonexistent/file.jsonl'))
        assert len(snippets) == 0

    def test_parse_invalid_json(self):
        """Test parsing file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('not valid json\n')
            f.write('{"code": "valid", "label": "safe"}\n')
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            # Should skip invalid line and process valid one
            assert len(snippets) == 1
        finally:
            os.unlink(temp_path)

class TestParseJuliet:
    def test_parse_juliet_c(self):
        """Test parsing Juliet C test cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bad file
            bad_file = Path(tmpdir) / "test_bad.c"
            bad_file.write_text("int main() { return 0; }")
            
            # Create a good file
            good_file = Path(tmpdir) / "test_good.c"
            good_file.write_text("int main() { return 0; }")
            
            snippets = parse_juliet_c_test_cases(Path(tmpdir))
            
            assert len(snippets) == 2
            vulnerable = [s for s in snippets if s['label'] == 'vulnerable']
            safe = [s for s in snippets if s['label'] == 'safe']
            assert len(vulnerable) == 1
            assert len(safe) == 1

    def test_parse_juliet_java(self):
        """Test parsing Juliet Java test cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bad file
            bad_file = Path(tmpdir) / "TestBad.java"
            bad_file.write_text("public class Test { }")
            
            # Create a good file
            good_file = Path(tmpdir) / "TestGood.java"
            good_file.write_text("public class Test { }")
            
            snippets = parse_juliet_java_test_cases(Path(tmpdir))
            
            assert len(snippets) == 2
            vulnerable = [s for s in snippets if s['label'] == 'vulnerable']
            safe = [s for s in snippets if s['label'] == 'safe']
            assert len(vulnerable) == 1
            assert len(safe) == 1

class TestCreateCodeSnippets:
    def test_create_snippets_from_parsed_data(self):
        """Test creating CodeSnippet entities from parsed data."""
        parsed_data = [
            {'code': 'print("hello")', 'label': 'vulnerable', 'language': 'Python', 'source': 'test'},
            {'code': 'print("world")', 'label': 'safe', 'language': 'Python', 'source': 'test'},
        ]
        
        snippets = create_code_snippets(parsed_data)
        
        assert len(snippets) == 2
        assert all(isinstance(s, CodeSnippet) for s in snippets)
        assert snippets[0].label == 'vulnerable'
        assert snippets[1].label == 'safe'

    def test_create_snippets_with_missing_labels(self):
        """Test creating snippets with missing labels."""
        parsed_data = [
            {'code': 'print("hello")', 'label': None, 'language': 'Python', 'source': 'test'},
        ]
        
        snippets = create_code_snippets(parsed_data)
        
        assert len(snippets) == 1
        assert snippets[0].label is None

class TestSaveSnippetsToCSV:
    def test_save_snippets_to_csv(self):
        """Test saving snippets to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "snippets.csv"
            
            snippets = [
                CodeSnippet(
                    snippet_id="test-1",
                    code="print('hello')",
                    language="Python",
                    label="vulnerable",
                    source="test",
                    file_path="test.py",
                    context="",
                    metadata={}
                ),
                CodeSnippet(
                    snippet_id="test-2",
                    code="print('world')",
                    language="Python",
                    label="safe",
                    source="test",
                    file_path="test.py",
                    context="",
                    metadata={}
                ),
            ]
            
            save_snippets_to_csv(snippets, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 3  # header + 2 snippets
                assert rows[0] == ['snippet_id', 'code', 'language', 'label', 'source', 'file_path', 'context', 'metadata']

class TestLogEdgeCases:
    def test_log_edge_cases(self):
        """Test logging edge cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "features.log"
            
            snippets = [
                CodeSnippet(
                    snippet_id="test-1",
                    code="print('hello')",
                    language="Python",
                    label="vulnerable",
                    source="test",
                    file_path="test.py",
                    context="",
                    metadata={}
                ),
                CodeSnippet(
                    snippet_id="test-2",
                    code="print('world')",
                    language="Python",
                    label=None,  # Missing label
                    source="test",
                    file_path="test.py",
                    context="",
                    metadata={}
                ),
            ]
            
            log_edge_cases(snippets, log_path)
            
            assert log_path.exists()
            with open(log_path, 'r') as f:
                content = f.read()
                assert "test-2" in content
                assert "NULL" in content
                assert "missing labels: 1" in content.lower()