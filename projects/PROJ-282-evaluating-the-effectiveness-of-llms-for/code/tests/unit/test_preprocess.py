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
    create_code_snippets,
    stratified_sample,
    save_snippets_to_parquet,
    save_labels_csv,
    log_edge_cases
)
from src.models.code_snippet import CodeSnippet, create_codesnippet

class TestPreprocessFunctions:
    def test_detect_language_from_extension(self):
        assert detect_language_from_extension("test.c") == "C"
        assert detect_language_from_extension("test.cpp") == "C++"
        assert detect_language_from_extension("test.py") == "Python"
        assert detect_language_from_extension("test.js") == "JavaScript"
        assert detect_language_from_extension("test.unknown") is None

    def test_normalize_label(self):
        assert normalize_label(1) == 1
        assert normalize_label(0) == 0
        assert normalize_label(True) == 1
        assert normalize_label(False) == 0
        assert normalize_label("vulnerable") == 1
        assert normalize_label("safe") == 0
        assert normalize_label("TRUE") == 1
        assert normalize_label("FALSE") == 0
        assert normalize_label(None) is None
        assert normalize_label("invalid") is None

    def test_extract_category_from_context(self):
        assert extract_category_from_context(78) == "CWE-78"
        assert extract_category_from_context("CWE-78") == "CWE-78"
        assert extract_category_from_context("78") == "CWE-78"
        assert extract_category_from_context("buffer-overflow") == "buffer-overflow"
        assert extract_category_from_context(None) is None

class TestCreateCodeSnippets:
    def test_create_snippets_success(self):
        raw_data = [
            {
                'code': 'int x = 0;',
                'language': 'C',
                'ground_truth_category': 78,
                'ground_truth_label': 1,
                'source_file': 'test.c'
            }
        ]
        dropped_log = []
        snippets = create_code_snippets(raw_data, dropped_log)
        
        assert len(snippets) == 1
        assert snippets[0].language == "C"
        assert snippets[0].ground_truth_category == "CWE-78"
        assert snippets[0].ground_truth_label == 1
        assert len(dropped_log) == 0

    def test_create_snippets_missing_label(self):
        raw_data = [
            {
                'code': 'int x = 0;',
                'language': 'C',
                'ground_truth_category': 78,
                'ground_truth_label': None,
                'source_file': 'test.c'
            }
        ]
        dropped_log = []
        snippets = create_code_snippets(raw_data, dropped_log)
        
        # Snippet should still be created, but logged as dropped for accuracy calc
        assert len(snippets) == 1
        assert snippets[0].ground_truth_label is None
        assert len(dropped_log) == 1
        assert dropped_log[0]['reason'] == 'missing_label'

class TestStratifiedSample:
    def test_stratified_sample_small_dataset(self):
        # Create small dataset with known distribution
        snippets = [
            create_codesnippet(f"snip_{i}", "code", "C", "CWE-78", 1 if i < 5 else 0)
            for i in range(10)
        ]
        
        sampled, stats = stratified_sample(snippets, max_samples=10)
        
        assert len(sampled) == 10
        assert stats['method'] == 'stratified'
        assert stats['total'] == 10

    def test_stratified_sample_larger_dataset(self):
        # Create larger dataset
        snippets = [
            create_codesnippet(f"snip_{i}", "code", "C", "CWE-78", 1 if i % 2 == 0 else 0)
            for i in range(100)
        ]
        
        sampled, stats = stratified_sample(snippets, max_samples=50)
        
        assert len(sampled) == 50
        assert stats['method'] == 'stratified'
        assert stats['total'] == 100
        assert stats['sampled'] == 50

class TestSaveFunctions:
    def test_save_snippets_to_parquet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            snippets = [
                create_codesnippet("snip_0", "code", "C", "CWE-78", 1),
                create_codesnippet("snip_1", "code", "Python", "CWE-89", 0)
            ]
            
            save_snippets_to_parquet(snippets, output_path)
            
            assert output_path.exists()
            df = pd.read_parquet(output_path)
            assert len(df) == 2
            assert 'snippet_id' in df.columns
            assert 'code' in df.columns

    def test_save_labels_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "labels.csv"
            snippets = [
                create_codesnippet("snip_0", "code", "C", "CWE-78", 1),
                create_codesnippet("snip_1", "code", "Python", "CWE-89", 0),
                create_codesnippet("snip_2", "code", "C", "CWE-78", None)  # Missing label
            ]
            
            save_labels_csv(snippets, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            # Header + 2 rows (snip_2 has None label, should be excluded)
            assert len(lines) == 3  # header + 2 data rows

    def test_log_edge_cases(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dropped.json"
            dropped_log = [
                {'snippet_id': 'snip_0', 'reason': 'missing_label'},
                {'snippet_id': 'snip_1', 'reason': 'validation_error: test'}
            ]
            
            log_edge_cases(dropped_log, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['snippet_id'] == 'snip_0'
            assert data[0]['reason'] == 'missing_label'