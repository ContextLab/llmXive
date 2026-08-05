import os
import sys
import tempfile
import json
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
from src.data.preprocess import (
    detect_language_from_extension,
    normalize_label,
    extract_category_from_context,
    create_code_snippets,
    stratified_sample,
    save_snippets_to_parquet,
    save_labels_csv,
    log_edge_cases
)
from src.models.code_snippet import CodeSnippet, CodeSnippetLanguageEnum, create_codesnippet

class TestDetectLanguage:
    def test_c_extension(self):
        assert detect_language_from_extension("test.c") == CodeSnippetLanguageEnum.C
    
    def test_cpp_extensions(self):
        assert detect_language_from_extension("test.cpp") == CodeSnippetLanguageEnum.CPP
        assert detect_language_from_extension("test.cc") == CodeSnippetLanguageEnum.CPP
    
    def test_js_extension(self):
        assert detect_language_from_extension("test.js") == CodeSnippetLanguageEnum.JS
    
    def test_unknown_extension(self):
        assert detect_language_from_extension("test.xyz") is None

class TestNormalizeLabel:
    def test_int_labels(self):
        assert normalize_label(1) == 1
        assert normalize_label(0) == 0
        assert normalize_label(2) == 1  # Non-zero is vulnerable
    
    def test_string_labels(self):
        assert normalize_label("vulnerable") == 1
        assert normalize_label("safe") == 0
        assert normalize_label("VULNERABLE") == 1
        assert normalize_label("SAFE") == 0
    
    def test_bool_labels(self):
        assert normalize_label(True) == 1
        assert normalize_label(False) == 0
    
    def test_none_label(self):
        assert normalize_label(None) is None

class TestExtractCategory:
    def test_buffer_overflow(self):
        assert "buffer_overflow" in extract_category_from_context("This is a buffer overflow test")
    
    def test_sql_injection(self):
        assert "sql_injection" in extract_category_from_context("SQL injection vulnerability")
    
    def test_no_match(self):
        assert extract_category_from_context("Normal code") == "unknown"

class TestCreateCodeSnippets:
    def test_valid_snippet_creation(self):
        raw_data = [
            {
                'id': 'test_1',
                'code': 'int x = 1;',
                'ground_truth_label': 1,
                'category': 'overflow',
                'language': 'C',
                'source_file': 'test.c'
            }
        ]
        snippets, edge_cases = create_code_snippets(raw_data, MagicMock())
        
        assert len(snippets) == 1
        assert len(edge_cases) == 0
        assert snippets[0].snippet_id == 'test_1'
        assert snippets[0].ground_truth_label == 1

    def test_missing_label_filtering(self):
        raw_data = [
            {
                'id': 'test_1',
                'code': 'int x = 1;',
                'ground_truth_label': None,
                'category': 'overflow',
                'language': 'C',
                'source_file': 'test.c'
            },
            {
                'id': 'test_2',
                'code': 'int y = 2;',
                'ground_truth_label': 0,
                'category': 'safe',
                'language': 'C',
                'source_file': 'test.c'
            }
        ]
        snippets, edge_cases = create_code_snippets(raw_data, MagicMock())
        
        assert len(snippets) == 1
        assert len(edge_cases) == 1
        assert edge_cases[0]['reason'] == 'missing_ground_truth_label'
        assert snippets[0].snippet_id == 'test_2'

    def test_string_label_normalization(self):
        raw_data = [
            {
                'id': 'test_1',
                'code': 'int x = 1;',
                'ground_truth_label': 'vulnerable',
                'category': 'overflow',
                'language': 'C',
                'source_file': 'test.c'
            }
        ]
        snippets, _ = create_code_snippets(raw_data, MagicMock())
        assert snippets[0].ground_truth_label == 1

class TestStratifiedSample:
    def test_stratification_logic(self):
        # Create a dataset with known distribution
        snippets = []
        # 10 C/overflow, 10 C/safe, 10 JS/overflow, 10 JS/safe
        for i in range(10):
            snippets.append(create_codesnippet(f"test_c_over_{i}", "code", CodeSnippetLanguageEnum.C, 1, "overflow", ""))
            snippets.append(create_codesnippet(f"test_c_safe_{i}", "code", CodeSnippetLanguageEnum.C, 0, "safe", ""))
            snippets.append(create_codesnippet(f"test_js_over_{i}", "code", CodeSnippetLanguageEnum.JS, 1, "overflow", ""))
            snippets.append(create_codesnippet(f"test_js_safe_{i}", "code", CodeSnippetLanguageEnum.JS, 0, "safe", ""))
        
        # Sample 8 total (2 per group)
        sampled = stratified_sample(snippets, max_samples=8, seed=42)
        
        assert len(sampled) == 8
        # Verify stratification: should have 2 from each of the 4 groups
        counts = {}
        for s in sampled:
            key = (s.language.value, s.ground_truth_category)
            counts[key] = counts.get(key, 0) + 1
        
        assert len(counts) == 4
        assert all(v == 2 for v in counts.values())

    def test_sample_size_limit(self):
        snippets = [create_codesnippet(f"test_{i}", "code", CodeSnippetLanguageEnum.C, 1, "overflow", "") for i in range(100)]
        sampled = stratified_sample(snippets, max_samples=10, seed=42)
        assert len(sampled) == 10

class TestSaveFunctions:
    def test_save_snippets_to_parquet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            snippets = [
                create_codesnippet("id1", "code1", CodeSnippetLanguageEnum.C, 1, "overflow", "file.c"),
                create_codesnippet("id2", "code2", CodeSnippetLanguageEnum.JS, 0, "safe", "file.js")
            ]
            
            save_snippets_to_parquet(snippets, output_path)
            
            assert output_path.exists()
            df = pd.read_parquet(output_path)
            assert len(df) == 2
            assert 'snippet_id' in df.columns
            assert 'code' in df.columns

    def test_save_labels_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            snippets = [
                create_codesnippet("id1", "code1", CodeSnippetLanguageEnum.C, 1, "overflow", "file.c"),
                create_codesnippet("id2", "code2", CodeSnippetLanguageEnum.JS, 0, "safe", "file.js")
            ]
            
            save_labels_csv(snippets, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
                assert "id1,1,overflow" in content
                assert "id2,0,safe" in content

    def test_log_edge_cases(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "edge_cases.json"
            edge_cases = [
                {"id": "bad1", "reason": "missing_label"},
                {"id": "bad2", "reason": "validation_error"}
            ]
            
            log_edge_cases(edge_cases, log_path)
            
            assert log_path.exists()
            with open(log_path, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]['id'] == 'bad1'