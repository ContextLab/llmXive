"""
Tests for correlation analysis module.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'code'))

from analysis.correlation import (
    load_file_metrics,
    filter_valid_rows,
    calculate_partial_correlation,
    run_correlation_analysis,
    save_results,
    main
)


def test_load_file_metrics():
    """Test loading CSV file with metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        csv_path = tmp_path / 'test_metrics.csv'
        
        # Create test CSV
        content = """file_path,mean_perplexity,mean_correctness,mean_complexity,mean_length,median_age
        test1.py,1.5,0.9,5.2,120.0,30.5
        test2.py,2.1,0.7,6.1,95.0,45.2
        test3.py,1.8,0.8,5.8,110.0,35.0
        """
        csv_path.write_text(content)
        
        data = load_file_metrics(csv_path)
        
        assert len(data) == 3
        assert data[0]['mean_perplexity'] == 1.5
        assert data[0]['median_age'] == 30.5
        assert data[1]['mean_correctness'] == 0.7


def test_filter_valid_rows():
    """Test filtering rows with NaN values."""
    data = [
        {'a': 1.0, 'b': 2.0, 'c': 3.0},
        {'a': np.nan, 'b': 2.0, 'c': 3.0},
        {'a': 1.0, 'b': 2.0, 'c': np.nan},
        {'a': 1.0, 'b': 2.0, 'c': 3.0},
    ]
    
    valid = filter_valid_rows(data, ['a', 'b', 'c'])
    
    assert len(valid) == 2
    assert valid[0]['a'] == 1.0
    assert valid[1]['c'] == 3.0


def test_calculate_partial_correlation():
    """Test partial correlation calculation."""
    # Create correlated data
    n = 100
    z = np.random.randn(n)
    x = z * 0.5 + np.random.randn(n) * 0.5
    y = z * 0.5 + x * 0.5 + np.random.randn(n) * 0.2
    
    r, p = calculate_partial_correlation(x, y, z)
    
    assert not np.isnan(r)
    assert 0 <= p <= 1
    # Partial correlation should be lower than simple correlation
    r_simple, _ = np.corrcoef(x, y)[0, 1], None
    assert abs(r) <= abs(np.corrcoef(x, y)[0, 1])


def test_run_correlation_analysis():
    """Test full correlation analysis pipeline."""
    # Create test data
    data = [
        {'median_age': 10.0, 'mean_perplexity': 1.2, 'mean_correctness': 0.9, 
         'mean_complexity': 5.0, 'mean_length': 100.0},
        {'median_age': 20.0, 'mean_perplexity': 1.5, 'mean_correctness': 0.8, 
         'mean_complexity': 6.0, 'mean_length': 120.0},
        {'median_age': 30.0, 'mean_perplexity': 1.8, 'mean_correctness': 0.7, 
         'mean_complexity': 7.0, 'mean_length': 140.0},
        {'median_age': 40.0, 'mean_perplexity': 2.1, 'mean_correctness': 0.6, 
         'mean_complexity': 8.0, 'mean_length': 160.0},
        {'median_age': 50.0, 'mean_perplexity': 2.4, 'mean_correctness': 0.5, 
         'mean_complexity': 9.0, 'mean_length': 180.0},
    ]
    
    results = run_correlation_analysis(data)
    
    assert results['status'] == 'success'
    assert results['n_samples'] == 5
    assert 'spearman_correlation_age_perplexity' in results
    assert 'p_value_age_perplexity' in results
    assert 'spearman_correlation_age_correctness' in results
    assert 'p_value_age_correctness' in results


def test_save_results():
    """Test saving results to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_path = tmp_path / 'results.json'
        
        results = {
            'status': 'success',
            'n_samples': 10,
            'spearman_correlation_age_perplexity': 0.85,
            'p_value_age_perplexity': 0.001
        }
        
        save_results(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['status'] == 'success'
        assert loaded['n_samples'] == 10
        assert loaded['spearman_correlation_age_perplexity'] == 0.85


def test_insufficient_data():
    """Test handling of insufficient data."""
    data = [
        {'median_age': 10.0, 'mean_perplexity': 1.2, 'mean_correctness': 0.9, 
         'mean_complexity': 5.0, 'mean_length': 100.0},
        {'median_age': 20.0, 'mean_perplexity': 1.5, 'mean_correctness': 0.8, 
         'mean_complexity': 6.0, 'mean_length': 120.0},
    ]
    
    results = run_correlation_analysis(data)
    
    assert results['status'] == 'insufficient_data'
    assert results['n_samples'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])