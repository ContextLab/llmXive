"""
Unit tests for correlation_analysis.py

Per spec.md Independent Test requirements for US2.
Tests Spearman coefficient computation and correlation analysis functions.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile
import json

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from correlation_analysis import (
    compute_spearman_correlation,
    compute_correlation_matrix,
    load_metrics_data,
    run_correlation_analysis,
    save_correlation_results
)

class TestComputeSpearmanCorrelation:
    """Tests for compute_spearman_correlation function"""
    
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated positive data"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        corr, p_value = compute_spearman_correlation(x, y)
        assert np.isclose(corr, 1.0, atol=0.01), f"Expected ~1.0, got {corr}"
        assert p_value < 0.05, "Expected significant p-value"
    
    def test_perfect_negative_correlation(self):
        """Test with perfectly correlated negative data"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        corr, p_value = compute_spearman_correlation(x, y)
        assert np.isclose(corr, -1.0, atol=0.01), f"Expected ~-1.0, got {corr}"
        assert p_value < 0.05, "Expected significant p-value"
    
    def test_no_correlation(self):
        """Test with uncorrelated data"""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        corr, p_value = compute_spearman_correlation(x, y)
        # With random data, correlation should be near 0
        assert abs(corr) < 0.3, f"Expected near 0 correlation, got {corr}"
    
    def test_nan_handling(self):
        """Test that NaN values are properly handled"""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, np.nan, 10.0])
        corr, p_value = compute_spearman_correlation(x, y)
        # Should still compute correlation from valid pairs
        assert not np.isnan(corr), "Correlation should be computed from valid pairs"
    
    def test_insufficient_data(self):
        """Test with insufficient data points"""
        x = np.array([1.0, 2.0])
        y = np.array([2.0, 4.0])
        corr, p_value = compute_spearman_correlation(x, y)
        assert np.isnan(corr), "Expected NaN for insufficient data"
    
    def test_inf_handling(self):
        """Test that Inf values are properly handled"""
        x = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, np.inf, 10.0])
        corr, p_value = compute_spearman_correlation(x, y)
        assert not np.isnan(corr), "Correlation should be computed from valid pairs"

class TestComputeCorrelationMatrix:
    """Tests for compute_correlation_matrix function"""
    
    def test_matrix_structure(self):
        """Test that correlation matrix has expected structure"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        z = np.array([3, 6, 9, 12, 15])
        
        results = compute_correlation_matrix(x, y, z)
        
        assert 'clone_density_vs_perplexity' in results
        assert 'clone_density_vs_accuracy' in results
        assert 'perplexity_vs_accuracy' in results
        
        # Check each result has required fields
        for key in results:
            if key != 'metadata':
                assert 'correlation' in results[key]
                assert 'p_value' in results[key]
                assert 'n_samples' in results[key]
                assert 'significant' in results[key]
    
    def test_significance_threshold(self):
        """Test that significance flag is set correctly"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        results = compute_correlation_matrix(x, y)
        assert results['clone_density_vs_perplexity']['significant'] is True
    
    def test_without_accuracy(self):
        """Test correlation matrix without accuracy data"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        results = compute_correlation_matrix(x, y, accuracy=None)
        assert 'clone_density_vs_accuracy' in results
        assert np.isnan(results['clone_density_vs_accuracy']['correlation'])

class TestSaveCorrelationResults:
    """Tests for save_correlation_results function"""
    
    def test_csv_output(self):
        """Test that CSV output is created correctly"""
        results = {
            'clone_density_vs_perplexity': {
                'correlation': 0.8,
                'p_value': 0.01,
                'n_samples': 100,
                'significant': True
            },
            'metadata': {
                'correlation_method': 'spearman'
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_results.csv'
            saved_path = save_correlation_results(results, output_path)
            
            assert saved_path.exists()
            df = pd.read_csv(saved_path)
            assert len(df) == 1
            assert df['metric_pair'].iloc[0] == 'clone_density_vs_perplexity'
            assert np.isclose(df['correlation'].iloc[0], 0.8)
    
    def test_json_output(self):
        """Test that JSON output is created correctly"""
        results = {
            'clone_density_vs_perplexity': {
                'correlation': 0.8,
                'p_value': 0.01,
                'n_samples': 100,
                'significant': True
            },
            'metadata': {
                'correlation_method': 'spearman'
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_results.csv'
            save_correlation_results(results, csv_path)
            
            json_path = csv_path.with_suffix('.json')
            assert json_path.exists()
            
            with open(json_path) as f:
                loaded = json.load(f)
            assert 'clone_density_vs_perplexity' in loaded
            assert loaded['clone_density_vs_perplexity']['correlation'] == 0.8