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
    create_code_snippets,
    save_snippets_to_csv,
    log_edge_cases,
    detect_language_from_extension,
    normalize_label,
    extract_category_from_context
)
from src.models.code_snippet import CodeSnippet, create_snippet


class TestNormalizeLabel:
    """Tests for label normalization."""

    def test_sql_injection_variants(self):
        """Test SQL injection label normalization."""
        assert normalize_label('sql') == 'SQLi'
        assert normalize_label('sql injection') == 'SQLi'
        assert normalize_label('sqli') == 'SQLi'
        assert normalize_label('SQL') == 'SQLi'

    def test_buffer_overflow_variants(self):
        """Test buffer overflow label normalization."""
        assert normalize_label('buffer overflow') == 'Buffer Overflow'
        assert normalize_label('overflow') == 'Buffer Overflow'
        assert normalize_label('bof') == 'Buffer Overflow'

    def test_xss_variants(self):
        """Test XSS label normalization."""
        assert normalize_label('xss') == 'XSS'
        assert normalize_label('cross-site scripting') == 'XSS'

    def test_unknown_label(self):
        """Test that unknown labels are preserved."""
        assert normalize_label('unknown_vuln') == 'unknown_vuln'
        assert normalize_label('') == 'unknown'
        assert normalize_label(None) == 'unknown'


class TestDetectLanguage:
    """Tests for language detection from file extensions."""

    def test_python_extension(self):
        """Test Python file detection."""
        assert detect_language_from_extension('test.py') == 'Python'
        assert detect_language_from_extension('/path/to/script.py') == 'Python'

    def test_c_extension(self):
        """Test C file detection."""
        assert detect_language_from_extension('test.c') == 'C'
        assert detect_language_from_extension('test.h') == 'C'

    def test_cpp_extension(self):
        """Test C++ file detection."""
        assert detect_language_from_extension('test.cpp') == 'C++'
        assert detect_language_from_extension('test.hpp') == 'C++'
        assert detect_language_from_extension('test.cc') == 'C++'

    def test_javascript_extension(self):
        """Test JavaScript file detection."""
        assert detect_language_from_extension('test.js') == 'JavaScript'
        assert detect_language_from_extension('test.ts') == 'JavaScript'

    def test_unknown_extension(self):
        """Test unknown file extension."""
        assert detect_language_from_extension('test.xyz') is None
        assert detect_language_from_extension('test') is None


class TestExtractCategory:
    """Tests for category extraction from context."""

    def test_sql_injection_context(self):
        """Test SQL injection category extraction."""
        assert extract_category_from_context('SQL injection vulnerability') == 'SQLi'
        assert extract_category_from_context('sqli in database') == 'SQLi'

    def test_buffer_overflow_context(self):
        """Test buffer overflow category extraction."""
        assert extract_category_from_context('buffer overflow in memory') == 'Buffer Overflow'
        assert extract_category_from_context('overflow detected') == 'Buffer Overflow'

    def test_no_match(self):
        """Test when no category matches."""
        assert extract_category_from_context('some random text') is None
        assert extract_category_from_context('') is None
        assert extract_category_from_context(None) is None


class TestParseVulDeePecker:
    """Tests for VulDeePecker JSONL parsing."""

    def test_parse_valid_jsonl(self):
        """Test parsing valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump({
                'id': 'test_001',
                'language': 'Python',
                'code': 'print("hello")',
                'label': 'vulnerable',
                'category': 'sql injection'
            }, f)
            f.write('\n')
            json.dump({
                'id': 'test_002',
                'language': 'C',
                'code': 'strcpy(buf, src);',
                'label': 'safe',
                'category': 'buffer overflow'
            }, f)
            f.write('\n')
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            assert len(snippets) == 2
            assert snippets[0]['id'] == 'test_001'
            assert snippets[0]['language'] == 'Python'
            assert snippets[0]['ground_truth_label'] == 'vulnerable'
            assert snippets[0]['ground_truth_category'] == 'SQLi'
        finally:
            temp_path.unlink()

    def test_parse_empty_file(self):
        """Test parsing empty JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            assert len(snippets) == 0
        finally:
            temp_path.unlink()

    def test_parse_missing_file(self):
        """Test parsing non-existent file."""
        snippets = parse_vuldeepecker_jsonl(Path('/nonexistent/file.jsonl'))
        assert len(snippets) == 0

    def test_parse_invalid_json(self):
        """Test parsing file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('not valid json\n')
            f.write('{"valid": "json"}\n')
            temp_path = Path(f.name)

        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            # Should skip invalid line and parse valid one
            assert len(snippets) == 1
        finally:
            temp_path.unlink()


class TestParseJuliet:
    """Tests for Juliet test case parsing."""

    def test_parse_c_test_cases(self):
        """Test parsing C test cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            testcases_dir = test_dir / 'testcases' / 'CWE89_001'
            testcases_dir.mkdir(parents=True)

            # Create test files
            (testcases_dir / 'goodG2B1.c').write_text('int main() { return 0; }')
            (testcases_dir / 'bad.c').write_text('strcpy(buf, src);')

            snippets = parse_juliet_c_test_cases(test_dir)
            
            # Should find 2 snippets
            assert len(snippets) == 2
            
            # Check labels
            labels = {s['id']: s['ground_truth_label'] for s in snippets}
            assert 'juliet_c_89_goodG2B1' in labels
            assert 'juliet_c_89_bad' in labels
            assert labels['juliet_c_89_bad'] == 'vulnerable'
            assert labels['juliet_c_89_goodG2B1'] == 'safe'

    def test_parse_missing_testcases_dir(self):
        """Test parsing when testcases directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            snippets = parse_juliet_c_test_cases(test_dir)
            assert len(snippets) == 0


class TestCreateCodeSnippets:
    """Tests for CodeSnippet entity creation."""

    def test_create_snippets_with_labels(self):
        """Test creating snippets with valid labels."""
        raw_data = [
            {
                'id': 'test_001',
                'language': 'Python',
                'source_code': 'print("hello")',
                'ground_truth_label': 'vulnerable',
                'ground_truth_category': 'SQLi',
                'source': 'test'
            }
        ]
        
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        assert snippets[0].id == 'test_001'
        assert snippets[0].language == 'Python'
        assert snippets[0].ground_truth_label == 'vulnerable'

    def test_create_snippets_missing_label(self):
        """Test creating snippets with missing labels."""
        raw_data = [
            {
                'id': 'test_002',
                'language': 'C',
                'source_code': 'int x = 0;',
                'ground_truth_label': None,
                'ground_truth_category': None,
                'source': 'test'
            }
        ]
        
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        assert getattr(snippets[0], '_label_missing', False) is True

    def test_create_snippets_empty_code(self):
        """Test creating snippets with empty code."""
        raw_data = [
            {
                'id': 'test_003',
                'language': 'Python',
                'source_code': '',
                'ground_truth_label': 'vulnerable',
                'ground_truth_category': 'SQLi',
                'source': 'test'
            }
        ]
        
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        assert getattr(snippets[0], '_malformed', False) is True


class TestSaveSnippetsToCSV:
    """Tests for saving snippets to CSV."""

    def test_save_snippets(self):
        """Test saving snippets to CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'snippets.csv'
            
            snippets = [
                create_snippet(
                    id='test_001',
                    language='Python',
                    source_code='print("hello")',
                    ground_truth_label='vulnerable',
                    ground_truth_category='SQLi'
                )
            ]
            
            save_snippets_to_csv(snippets, output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert 'test_001' in content
            assert 'Python' in content
            assert 'vulnerable' in content

    def test_save_snippets_with_missing_label(self):
        """Test saving snippets with missing labels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'snippets.csv'
            
            snippet = create_snippet(
                id='test_002',
                language='C',
                source_code='int x = 0;',
                ground_truth_label=None,
                ground_truth_category=None
            )
            snippet._label_missing = True
            
            save_snippets_to_csv([snippet], output_path)
            
            content = output_path.read_text()
            assert 'label_missing' in content
            assert 'True' in content


class TestLogEdgeCases:
    """Tests for logging edge cases."""

    def test_log_edge_cases(self):
        """Test logging edge cases to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'edge_cases.json'
            
            edge_cases = [
                {'id': 'test_001', 'issue': 'missing_label', 'language': 'Python'},
                {'id': 'test_002', 'issue': 'empty_code', 'language': 'C'}
            ]
            
            log_edge_cases(edge_cases, log_path)
            
            assert log_path.exists()
            with open(log_path, 'r') as f:
                logged = json.load(f)
                assert len(logged) == 2
                assert logged[0]['issue'] == 'missing_label'
                assert logged[1]['issue'] == 'empty_code'

    def test_log_empty_edge_cases(self):
        """Test logging empty edge cases list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'edge_cases.json'
            
            log_edge_cases([], log_path)
            
            assert log_path.exists()
            content = log_path.read_text()
            assert content == '[]'