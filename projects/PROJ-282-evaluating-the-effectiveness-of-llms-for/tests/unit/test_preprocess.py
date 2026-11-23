"""
Unit tests for the preprocessing module.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

from src.data.preprocess import (
    detect_language_from_extension,
    normalize_label,
    extract_category_from_context,
    parse_bigvul_directory,
    parse_raw_directory,
    create_code_snippets,
    stratified_sample,
    save_snippets_to_parquet,
    save_labels_csv,
    log_edge_cases
)
from src.models.code_snippet import CodeSnippet, CodeSnippetLanguageEnum, create_codesnippet

class TestLanguageDetection:
    def test_c_extension(self):
        assert detect_language_from_extension("test.c") == "C"
    
    def test_cpp_extension(self):
        assert detect_language_from_extension("test.cpp") == "C++"
        assert detect_language_from_extension("test.cc") == "C++"
    
    def test_js_extension(self):
        assert detect_language_from_extension("test.js") == "JavaScript"
    
    def test_unknown_extension(self):
        assert detect_language_from_extension("test.xyz") is None

class TestLabelNormalization:
    def test_valid_zero(self):
        assert normalize_label(0) == 0
    
    def test_valid_one(self):
        assert normalize_label(1) == 1
    
    def test_positive_int(self):
        assert normalize_label(5) == 1
    
    def test_negative_int(self):
        assert normalize_label(-1) is None
    
    def test_string_valid(self):
        assert normalize_label("1") == 1
        assert normalize_label("0") == 0
    
    def test_none(self):
        assert normalize_label(None) is None
    
    def test_invalid_string(self):
        assert normalize_label("vulnerable") is None

class TestCategoryExtraction:
    def test_cwe_pattern(self):
        assert extract_category_from_context("CWE-79: XSS") == "CWE-79"
    
    def test_cwe_lowercase(self):
        assert extract_category_from_context("cwe-123: buffer overflow") == "CWE-123"
    
    def test_no_cwe(self):
        assert extract_category_from_context("Some other text") is None
    
    def test_empty(self):
        assert extract_category_from_context("") is None

class TestSnippetCreation:
    def test_create_valid_snippet(self):
        raw_data = [
            {
                'snippet_id': 'test_1',
                'language': 'C',
                'code': 'int main() { return 0; }',
                'ground_truth_label': 1,
                'ground_truth_category': 'CWE-119',
                'source_file': 'test.c',
                'line_number': 10,
                'function_name': 'main',
                'raw_context': None
            }
        ]
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        assert snippets[0].snippet_id == 'test_1'
        assert snippets[0].ground_truth_label == 1
        assert snippets[0].language == CodeSnippetLanguageEnum.C

    def test_skip_invalid_label(self):
        raw_data = [
            {
                'snippet_id': 'test_1',
                'language': 'C',
                'code': 'int main() { return 0; }',
                'ground_truth_label': None,  # Missing label
                'ground_truth_category': None,
                'source_file': None,
                'line_number': None,
                'function_name': None,
                'raw_context': None
            }
        ]
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 0

    def test_unknown_language(self):
        raw_data = [
            {
                'snippet_id': 'test_1',
                'language': 'UnknownLang',
                'code': 'int main() { return 0; }',
                'ground_truth_label': 0,
                'ground_truth_category': None,
                'source_file': None,
                'line_number': None,
                'function_name': None,
                'raw_context': None
            }
        ]
        snippets = create_code_snippets(raw_data)
        assert len(snippets) == 1
        assert snippets[0].language == CodeSnippetLanguageEnum.OTHER

class TestStratifiedSampling:
    def test_empty_input(self):
        assert stratified_sample([]) == []

    def test_no_sampling_needed(self):
        snippets = [
            create_codesnippet('1', CodeSnippetLanguageEnum.C, 'code1', 1),
            create_codesnippet('2', CodeSnippetLanguageEnum.C, 'code2', 0),
        ]
        sampled = stratified_sample(snippets, max_samples=10)
        assert len(sampled) == 2

    def test_sampling_reduction(self):
        # Create 100 snippets
        snippets = [
            create_codesnippet(str(i), CodeSnippetLanguageEnum.C, f'code{i}', i % 2)
            for i in range(100)
        ]
        sampled = stratified_sample(snippets, max_samples=10)
        assert len(sampled) == 10

    def test_language_stratification(self):
        # Create balanced dataset
        snippets = []
        for i in range(50):
            snippets.append(create_codesnippet(f'c_{i}', CodeSnippetLanguageEnum.C, f'c{i}', 1))
        for i in range(50):
            snippets.append(create_codesnippet(f'js_{i}', CodeSnippetLanguageEnum.JAVASCRIPT, f'js{i}', 0))
        
        sampled = stratified_sample(snippets, max_samples=20, by_language=True)
        
        # Should have roughly equal representation
        c_count = sum(1 for s in sampled if s.language == CodeSnippetLanguageEnum.C)
        js_count = sum(1 for s in sampled if s.language == CodeSnippetLanguageEnum.JAVASCRIPT)
        
        # Allow some variance due to random sampling
        assert 5 <= c_count <= 15
        assert 5 <= js_count <= 15

class TestOutputFunctions:
    def test_save_parquet(self, tmp_path):
        snippets = [
            create_codesnippet('1', CodeSnippetLanguageEnum.C, 'code1', 1),
            create_codesnippet('2', CodeSnippetLanguageEnum.C, 'code2', 0),
        ]
        output_path = tmp_path / "test.parquet"
        save_snippets_to_parquet(snippets, output_path)
        
        assert output_path.exists()
        df = pd.read_parquet(output_path)
        assert len(df) == 2
        assert 'snippet_id' in df.columns
        assert 'code' in df.columns

    def test_save_labels_csv(self, tmp_path):
        snippets = [
            create_codesnippet('1', CodeSnippetLanguageEnum.C, 'code1', 1, 'CWE-119'),
            create_codesnippet('2', CodeSnippetLanguageEnum.C, 'code2', 0),
        ]
        output_path = tmp_path / "labels.csv"
        save_labels_csv(snippets, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'snippet_id,ground_truth_label,ground_truth_category' in content
            assert '1,1,CWE-119' in content
            assert '2,0,' in content

    def test_log_edge_cases(self, tmp_path):
        snippets = [
            create_codesnippet('1', CodeSnippetLanguageEnum.C, 'code1', 1, 'CWE-119'),
            create_codesnippet('2', CodeSnippetLanguageEnum.C, 'code2', 0),
        ]
        log_path = tmp_path / "stats.json"
        stats = log_edge_cases(snippets, log_path)
        
        assert log_path.exists()
        assert stats['total_snippets'] == 2
        assert stats['by_label'][1] == 1
        assert stats['by_label'][0] == 1