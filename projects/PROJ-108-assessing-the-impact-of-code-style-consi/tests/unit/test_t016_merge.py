"""
Unit tests for T016: Merge and finalize style scores.

Tests the logic of merging raw scores, metadata, and stratification groups.
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
CODE_DIR = Path(__file__).parent.parent / 'code'
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from code_04_merge_and_finalize_scores import merge_datasets, save_final_csv, load_sensitivity_report

def test_merge_datasets_basic():
    """Test basic merging of three datasets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock raw scores
        raw_scores_path = tmpdir / 'raw_scores.csv'
        with open(raw_scores_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'pylint_indent', 'radon_line_len', 'composite_score'])
            writer.writeheader()
            writer.writerow({'file_path': 'file1.py', 'pylint_indent': 0.8, 'radon_line_len': 0.9, 'composite_score': 0.85})
            writer.writerow({'file_path': 'file2.py', 'pylint_indent': 0.3, 'radon_line_len': 0.4, 'composite_score': 0.35})
        
        # Create mock metadata
        metadata_path = tmpdir / 'metadata.csv'
        with open(metadata_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'file_size', 'cyclomatic_complexity', 'file_age'])
            writer.writeheader()
            writer.writerow({'file_path': 'file1.py', 'file_size': 1024, 'cyclomatic_complexity': 5, 'file_age': 30})
            writer.writerow({'file_path': 'file2.py', 'file_size': 2048, 'cyclomatic_complexity': 10, 'file_age': 60})
        
        # Create mock stratified data
        stratified_path = tmpdir / 'stratified.csv'
        with open(stratified_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'group'])
            writer.writeheader()
            writer.writerow({'file_path': 'file1.py', 'group': 'High'})
            writer.writerow({'file_path': 'file2.py', 'group': 'Low'})
        
        # Merge
        result = merge_datasets(raw_scores_path, metadata_path, stratified_path)
        
        # Assertions
        assert len(result) == 2
        
        file1 = next(r for r in result if r['file_path'] == 'file1.py')
        assert file1['pylint_indent'] == 0.8
        assert file1['file_size'] == 1024
        assert file1['group'] == 'High'
        
        file2 = next(r for r in result if r['file_path'] == 'file2.py')
        assert file2['composite_score'] == 0.35
        assert file2['cyclomatic_complexity'] == 10
        assert file2['group'] == 'Low'

def test_merge_datasets_missing_files():
    """Test merging when some files are missing for certain records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Raw scores only
        raw_scores_path = tmpdir / 'raw_scores.csv'
        with open(raw_scores_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'composite_score'])
            writer.writeheader()
            writer.writerow({'file_path': 'file1.py', 'composite_score': 0.5})
            writer.writerow({'file_path': 'file2.py', 'composite_score': 0.5})
        
        # Metadata only for file1
        metadata_path = tmpdir / 'metadata.csv'
        with open(metadata_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'file_size'])
            writer.writeheader()
            writer.writerow({'file_path': 'file1.py', 'file_size': 100})
        
        # Stratified only for file1
        stratified_path = tmpdir / 'stratified.csv'
        with open(stratified_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'group'])
            writer.writeheader()
            writer.writerow({'file_path': 'file1.py', 'group': 'Medium'})
        
        result = merge_datasets(raw_scores_path, metadata_path, stratified_path)
        
        assert len(result) == 2
        
        file1 = next(r for r in result if r['file_path'] == 'file1.py')
        assert file1['file_size'] == 100
        assert file1['group'] == 'Medium'
        
        file2 = next(r for r in result if r['file_path'] == 'file2.py')
        assert file2.get('file_size') is None
        assert file2['group'] == 'Unknown'  # Should fall back to Unknown or re-calc

def test_save_final_csv_columns():
    """Test that save_final_csv writes the correct columns in the correct order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        output_path = tmpdir / 'output.csv'
        
        data = [
            {
                'file_path': 'test.py',
                'pylint_indent': 0.5,
                'radon_line_len': 0.6,
                'composite_score': 0.55,
                'group': 'Medium',
                'file_size': 500,
                'cyclomatic_complexity': 3,
                'file_age': 10
            }
        ]
        
        save_final_csv(data, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            expected_headers = [
                'file_path', 'pylint_indent', 'radon_line_len', 'composite_score',
                'group', 'file_size', 'cyclomatic_complexity', 'file_age'
            ]
            
            assert headers == expected_headers
            
            row = next(reader)
            assert row['file_path'] == 'test.py'
            assert row['composite_score'] == '0.55'
            assert row['group'] == 'Medium'

def test_load_sensitivity_report_missing():
    """Test loading sensitivity report when file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / 'missing.json'
        result = load_sensitivity_report(report_path)
        
        assert 'optimal_thresholds' in result
        assert result['optimal_thresholds']['low'] == 0.25
        assert result['optimal_thresholds']['high'] == 0.75