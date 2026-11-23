"""
Unit tests for generate_statistical_report.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_statistical_report import (
    load_per_sample_errors,
    generate_method_pairs,
    run_statistical_tests
)
from stats.significance import run_paired_wilcoxon


class TestLoadPerSampleErrors:
    """Tests for load_per_sample_errors function."""
    
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid per_sample_errors.csv file."""
        # Create test data
        data = {
            'sample_id': ['s1', 's2', 's3', 's4'],
            'method': ['m1', 'm1', 'm2', 'm2'],
            'prediction': [1.0, 2.0, 1.5, 2.5],
            'lower_bound': [0.5, 1.5, 1.0, 2.0],
            'upper_bound': [1.5, 2.5, 2.0, 3.0],
            'ground_truth': [1.1, 2.1, 1.6, 2.6],
            'dataset': ['d1', 'd1', 'd1', 'd1']
        }
        df = pd.DataFrame(data)
        
        # Save to temp file
        filepath = tmp_path / "per_sample_errors.csv"
        df.to_csv(filepath, index=False)
        
        # Load and verify
        loaded_df = load_per_sample_errors(filepath)
        
        assert len(loaded_df) == 4
        assert set(loaded_df.columns) == set(data.keys())
        assert loaded_df['dataset'].unique()[0] == 'd1'
    
    def test_missing_columns(self, tmp_path):
        """Test that missing columns raise an error."""
        # Create data with missing column
        data = {
            'sample_id': ['s1', 's2'],
            'method': ['m1', 'm2'],
            'prediction': [1.0, 2.0],
            'ground_truth': [1.1, 2.1]
            # Missing: lower_bound, upper_bound, dataset
        }
        df = pd.DataFrame(data)
        
        filepath = tmp_path / "per_sample_errors.csv"
        df.to_csv(filepath, index=False)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            load_per_sample_errors(filepath)
    
    def test_file_not_found(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        filepath = tmp_path / "nonexistent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_per_sample_errors(filepath)


class TestGenerateMethodPairs:
    """Tests for generate_method_pairs function."""
    
    def test_two_methods(self):
        """Test with two methods."""
        methods = ['m1', 'm2']
        pairs = generate_method_pairs(methods)
        
        assert len(pairs) == 1
        assert pairs[0] == ('m1', 'm2')
    
    def test_three_methods(self):
        """Test with three methods."""
        methods = ['m1', 'm2', 'm3']
        pairs = generate_method_pairs(methods)
        
        assert len(pairs) == 3
        assert ('m1', 'm2') in pairs
        assert ('m1', 'm3') in pairs
        assert ('m2', 'm3') in pairs
    
    def test_empty_list(self):
        """Test with empty list."""
        pairs = generate_method_pairs([])
        assert len(pairs) == 0
    
    def test_single_method(self):
        """Test with single method."""
        pairs = generate_method_pairs(['m1'])
        assert len(pairs) == 0


class TestRunStatisticalTests:
    """Tests for run_statistical_tests function."""
    
    def test_single_dataset_two_methods(self):
        """Test with one dataset and two methods."""
        # Create test data with known differences
        np.random.seed(42)
        n_samples = 100
        
        data = []
        for i in range(n_samples):
            # Method 1: errors around 0
            data.append({
                'sample_id': f's{i}',
                'method': 'm1',
                'prediction': 1.0 + np.random.normal(0, 0.1),
                'lower_bound': 0.8,
                'upper_bound': 1.2,
                'ground_truth': 1.0,
                'dataset': 'd1'
            })
            # Method 2: errors around 0.5 (systematically different)
            data.append({
                'sample_id': f's{i}',
                'method': 'm2',
                'prediction': 1.5 + np.random.normal(0, 0.1),
                'lower_bound': 1.3,
                'upper_bound': 1.7,
                'ground_truth': 1.0,
                'dataset': 'd1'
            })
        
        df = pd.DataFrame(data)
        
        # Run tests
        results = run_statistical_tests(df)
        
        assert len(results) == 1
        assert results['dataset'].iloc[0] == 'd1'
        assert 'm1 vs m2' in results['method_pair'].iloc[0]
        assert results['test_type'].iloc[0] == 'paired_wilcoxon'
        assert pd.notna(results['p_value'].iloc[0])
        assert results['significance_flag'].iloc[0] in ['significant', 'not_significant']
    
    def test_multiple_datasets(self):
        """Test with multiple datasets."""
        data = []
        for dataset in ['d1', 'd2']:
            for i in range(50):
                data.append({
                    'sample_id': f'{dataset}_s{i}',
                    'method': 'm1',
                    'prediction': 1.0,
                    'lower_bound': 0.8,
                    'upper_bound': 1.2,
                    'ground_truth': 1.0,
                    'dataset': dataset
                })
                data.append({
                    'sample_id': f'{dataset}_s{i}',
                    'method': 'm2',
                    'prediction': 1.0,
                    'lower_bound': 0.8,
                    'upper_bound': 1.2,
                    'ground_truth': 1.0,
                    'dataset': dataset
                })
        
        df = pd.DataFrame(data)
        results = run_statistical_tests(df)
        
        assert len(results) == 2  # One pair per dataset
        assert set(results['dataset'].unique()) == {'d1', 'd2'}
    
    def test_inconclusive_small_sample(self):
        """Test with very small sample size."""
        data = []
        for i in range(5):  # Only 5 samples
            data.append({
                'sample_id': f's{i}',
                'method': 'm1',
                'prediction': 1.0,
                'lower_bound': 0.8,
                'upper_bound': 1.2,
                'ground_truth': 1.0,
                'dataset': 'd1'
            })
            data.append({
                'sample_id': f's{i}',
                'method': 'm2',
                'prediction': 1.0,
                'lower_bound': 0.8,
                'upper_bound': 1.2,
                'ground_truth': 1.0,
                'dataset': 'd1'
            })
        
        df = pd.DataFrame(data)
        results = run_statistical_tests(df)
        
        assert len(results) == 1
        assert results['significance_flag'].iloc[0] == 'inconclusive'
    
    def test_multiple_methods(self):
        """Test with three methods (should generate 3 pairs)."""
        data = []
        for i in range(100):
            for method in ['m1', 'm2', 'm3']:
                data.append({
                    'sample_id': f's{i}',
                    'method': method,
                    'prediction': 1.0,
                    'lower_bound': 0.8,
                    'upper_bound': 1.2,
                    'ground_truth': 1.0,
                    'dataset': 'd1'
                })
        
        df = pd.DataFrame(data)
        results = run_statistical_tests(df)
        
        assert len(results) == 3  # 3 pairs: m1-m2, m1-m3, m2-m3