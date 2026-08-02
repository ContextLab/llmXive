"""
Unit tests for the preprocess module.

Tests cover:
- Language detection
- Label normalization
- Category extraction
- Snippet creation
- Stratified sampling
- CSV saving
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.data.preprocess import (
    detect_language_from_extension,
    normalize_label,
    extract_category_from_context,
    create_code_snippets,
    stratified_sample,
    save_snippets_to_csv,
    parse_vuldeepecker_jsonl,
    parse_bigvul_directory,
    parse_juliet_c_test_cases
)
from src.models.code_snippet import CodeSnippet, create_codesnippet

class TestLanguageDetection:
    def test_detect_c_extension(self):
        assert detect_language_from_extension("test.c") == "C"
        assert detect_language_from_extension("test.cpp") == "C"
        assert detect_language_from_extension("test.h") == "C"

    def test_detect_python_extension(self):
        assert detect_language_from_extension("test.py") == "Python"

    def test_detect_js_extension(self):
        assert detect_language_from_extension("test.js") == "JavaScript"
        assert detect_language_from_extension("test.jsx") == "JavaScript"

    def test_detect_unknown_extension(self):
        assert detect_language_from_extension("test.xyz") is None

class TestLabelNormalization:
    def test_vulnerable_labels(self):
        assert normalize_label("Vulnerable") == "Vulnerable"
        assert normalize_label("vulnerable") == "Vulnerable"
        assert normalize_label("Unsafe") == "Vulnerable"
        assert normalize_label("VULN") == "Vulnerable"

    def test_safe_labels(self):
        assert normalize_label("Safe") == "Safe"
        assert normalize_label("safe") == "Safe"
        assert normalize_label("Clean") == "Safe"
        assert normalize_label("Benign") == "Safe"
        assert normalize_label("No") == "Safe"

    def test_none_label(self):
        assert normalize_label(None) == "Safe"
        assert normalize_label("") == "Safe"

    def test_uncertain_labels(self):
        assert normalize_label("Unknown") == "Uncertain"
        assert normalize_label("Maybe") == "Uncertain"

class TestCategoryExtraction:
    def test_sqli_detection(self):
        context = "SQL injection vulnerability in query"
        assert extract_category_from_context(context, "Python") == "SQLi"

    def test_buffer_overflow_detection(self):
        context = "Buffer overflow in strcpy"
        assert extract_category_from_context(context, "C") == "Buffer Overflow"

    def test_command_injection_detection(self):
        context = "Command injection via system call"
        assert extract_category_from_context(context, "Python") == "Command Injection"

    def test_no_category(self):
        context = "Normal code"
        assert extract_category_from_context(context, "Python") == "None"

class TestSnippetCreation:
    def test_create_snippet_success(self):
        raw_data = [
            {
                'source': 'Test',
                'code': 'print("hello")',
                'label': 'Vulnerable',
                'category': 'SQLi',
                'language': 'Python'
            }
        ]
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        assert snippets[0].language == "Python"
        assert snippets[0].ground_truth_label == "Vulnerable"
        assert snippets[0].ground_truth_category == "SQLi"

    def test_skip_invalid_language(self):
        raw_data = [
            {
                'source': 'Test',
                'code': 'print("hello")',
                'label': 'Vulnerable',
                'category': 'SQLi',
                'language': 'Java'  # Invalid for our pipeline
            }
        ]
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 0

    def test_missing_label_handling(self):
        raw_data = [
            {
                'source': 'Test',
                'code': 'print("hello")',
                'label': None,
                'category': 'None',
                'language': 'Python'
            }
        ]
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        # None label should normalize to "Safe"
        assert snippets[0].ground_truth_label == "Safe"

class TestStratifiedSampling:
    def test_no_sampling_needed(self):
        snippets = [
            create_codesnippet("1", "Python", "code1", "Vulnerable", "SQLi"),
            create_codesnippet("2", "C", "code2", "Safe", "None")
        ]
        sampled = stratified_sample(snippets, max_samples=100)
        assert len(sampled) == 2

    def test_stratified_reduction(self):
        # Create 1000 snippets across 2 languages and 2 categories
        snippets = []
        for i in range(500):
            snippets.append(create_codesnippet(f"p{i}", "Python", f"code{i}", "Vulnerable", "SQLi"))
        for i in range(500):
            snippets.append(create_codesnippet(f"c{i}", "C", f"code{i}", "Safe", "None"))
        
        sampled = stratified_sample(snippets, max_samples=100)
        assert len(sampled) == 100
        # Check proportional representation
        python_count = sum(1 for s in sampled if s.language == "Python")
        c_count = sum(1 for s in sampled if s.language == "C")
        # Should be roughly 50/50
        assert 40 <= python_count <= 60
        assert 40 <= c_count <= 60

    def test_stratified_by_category(self):
        snippets = []
        # 400 SQLi, 100 Buffer Overflow
        for i in range(400):
            snippets.append(create_codesnippet(f"s{i}", "Python", f"code{i}", "Vulnerable", "SQLi"))
        for i in range(100):
            snippets.append(create_codesnippet(f"b{i}", "Python", f"code{i}", "Vulnerable", "Buffer Overflow"))
        
        sampled = stratified_sample(snippets, max_samples=100)
        # Should preserve ratio roughly
        sqli_count = sum(1 for s in sampled if s.ground_truth_category == "SQLi")
        bo_count = sum(1 for s in sampled if s.ground_truth_category == "Buffer Overflow")
        assert sqli_count + bo_count == 100
        assert sqli_count > bo_count  # SQLi should be more represented

class TestCSVSaving:
    def test_save_predictions_no_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "predictions.csv"
            snippets = [
                create_codesnippet("1", "Python", "code1", "Vulnerable", "SQLi"),
                create_codesnippet("2", "C", "code2", "Safe", "None")
            ]
            count = save_snippets_to_csv(snippets, output_path, include_missing=False)
            assert count == 2
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 3  # Header + 2 rows

    def test_save_features_with_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "features.csv"
            snippets = [
                create_codesnippet("1", "Python", "code1", "Vulnerable", "SQLi"),
                create_codesnippet("2", "Python", "code2", "Uncertain", "None")  # Missing label
            ]
            count = save_snippets_to_csv(snippets, output_path, include_missing=True)
            assert count == 2
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) == 2
            assert rows[1]['label_missing'] == 'True'

    def test_empty_snippets_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.csv"
            count = save_snippets_to_csv([], output_path, include_missing=True)
            assert count == 0
            assert output_path.exists()

class TestParsingFunctions:
    @patch('builtins.open', new_callable=MagicMock)
    def test_parse_vuldeepecker_jsonl(self, mock_open):
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.__iter__ = MagicMock(return_value=iter([
            '{"code": "print(1)", "label": "Vulnerable"}\n',
            '{"code": "print(2)", "label": "Safe"}\n'
        ]))
        mock_open.return_value = mock_file
        
        snippets = parse_vuldeepecker_jsonl(Path("dummy.jsonl"))
        assert len(snippets) == 2
        assert snippets[0]['language'] == "Python"

    @patch('builtins.open', new_callable=MagicMock)
    @patch('pathlib.Path.glob', return_value=[Path("dummy.json")])
    def test_parse_bigvul_directory(self, mock_glob, mock_open):
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.read.return_value = json.dumps([
            {"code": "int x;", "label": "Vulnerable", "type": "Buffer Overflow", "language": "C"}
        ])
        mock_open.return_value = mock_file
        
        snippets = parse_bigvul_directory(Path("dummy_dir"))
        assert len(snippets) == 1
        assert snippets[0]['language'] == "C"

    @patch('builtins.open', new_callable=MagicMock)
    def test_parse_juliet_c_test_cases(self, mock_open):
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.read.return_value = "/* BAD */ int x = 0;"
        mock_open.return_value = mock_file
        
        snippets = parse_juliet_c_test_cases(Path("dummy.c"))
        assert len(snippets) == 1
        assert snippets[0]['label'] == "Vulnerable"
        assert snippets[0]['language'] == "C"

class TestEdgeCases:
    def test_empty_code_snippet(self):
        raw_data = [
            {
                'source': 'Test',
                'code': '',
                'label': 'Vulnerable',
                'category': 'SQLi',
                'language': 'Python'
            }
        ]
        snippets = create_code_snippets(raw_data)
        # Empty code might be allowed or filtered; check behavior
        # Based on implementation, it should create the snippet
        assert len(snippets) == 1

    def test_very_long_code(self):
        long_code = "x = 1\n" * 10000
        raw_data = [
            {
                'source': 'Test',
                'code': long_code,
                'label': 'Vulnerable',
                'category': 'SQLi',
                'language': 'Python'
            }
        ]
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        assert len(snippets[0].source_code) == len(long_code)

    def test_malformed_json_in_parsing(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"code": "valid"}\n')
            f.write('invalid json\n')
            f.write('{"code": "also valid"}\n')
            temp_path = Path(f.name)
        
        try:
            snippets = parse_vuldeepecker_jsonl(temp_path)
            # Should skip the invalid line
            assert len(snippets) == 2
        finally:
            temp_path.unlink()
