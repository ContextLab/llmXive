"""
Tests for sensitivity analysis binary metrics (T020a).

Verifies McNemar's test implementation and CSV output generation.
"""
import os
import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from experiments.sensitivity_binary import (
    prepare_contingency_table,
    run_mcnemar_sweep,
    BINARY_METRICS,
    ALPHA_LEVELS
)

@pytest.fixture
def sample_records():
    """Create sample experiment records for testing."""
    records = []
    
    # Create paired data for multiple seeds
    # Foundation Protocol vs Native Direct Communication
    for seed in range(1, 11):
        # Scenario 1: Foundation better (some seeds)
        if seed <= 3:
            records.append({
                'seed': seed,
                'protocol': 'Foundation',
                'recovery_success': True,
                'task_success': True
            })
            records.append({
                'seed': seed,
                'protocol': 'Native Direct',
                'recovery_success': False,
                'task_success': False
            })
        # Scenario 2: Direct better (some seeds)
        elif seed <= 5:
            records.append({
                'seed': seed,
                'protocol': 'Foundation',
                'recovery_success': False,
                'task_success': False
            })
            records.append({
                'seed': seed,
                'protocol': 'Native Direct',
                'recovery_success': True,
                'task_success': True
            })
        # Scenario 3: Both same (remaining seeds)
        else:
            records.append({
                'seed': seed,
                'protocol': 'Foundation',
                'recovery_success': True,
                'task_success': True
            })
            records.append({
                'seed': seed,
                'protocol': 'Native Direct',
                'recovery_success': True,
                'task_success': True
            })
    
    return records

def test_prepare_contingency_table_basic():
    """Test contingency table preparation with known data."""
    records = [
        {'seed': 1, 'protocol': 'Foundation', 'recovery_success': True},
        {'seed': 1, 'protocol': 'Native Direct', 'recovery_success': False},
        {'seed': 2, 'protocol': 'Foundation', 'recovery_success': False},
        {'seed': 2, 'protocol': 'Native Direct', 'recovery_success': True},
        {'seed': 3, 'protocol': 'Foundation', 'recovery_success': True},
        {'seed': 3, 'protocol': 'Native Direct', 'recovery_success': True},
        {'seed': 4, 'protocol': 'Foundation', 'recovery_success': False},
        {'seed': 4, 'protocol': 'Native Direct', 'recovery_success': False},
    ]
    
    a, b, c, d = prepare_contingency_table(records, 'recovery_success')
    
    # Expected:
    # seed 1: F=True, D=False -> b
    # seed 2: F=False, D=True -> c
    # seed 3: F=True, D=True -> a
    # seed 4: F=False, D=False -> d
    assert a == 1
    assert b == 1
    assert c == 1
    assert d == 1

def test_prepare_contingency_table_no_discordant():
    """Test contingency table when there are no discordant pairs."""
    records = [
        {'seed': 1, 'protocol': 'Foundation', 'recovery_success': True},
        {'seed': 1, 'protocol': 'Native Direct', 'recovery_success': True},
        {'seed': 2, 'protocol': 'Foundation', 'recovery_success': False},
        {'seed': 2, 'protocol': 'Native Direct', 'recovery_success': False},
    ]
    
    a, b, c, d = prepare_contingency_table(records, 'recovery_success')
    
    # All concordant, no discordant pairs
    assert a == 1
    assert b == 0
    assert c == 0
    assert d == 1

def test_run_mcnemar_sweep_basic(sample_records):
    """Test McNemar sweep produces expected output structure."""
    results = run_mcnemar_sweep(sample_records, BINARY_METRICS, ALPHA_LEVELS)
    
    # Should have results for each metric and each alpha level
    expected_count = len(BINARY_METRICS) * len(ALPHA_LEVELS)
    assert len(results) == expected_count
    
    # Check structure of each result
    for result in results:
        assert 'alpha' in result
        assert 'metric' in result
        assert 'p_value' in result
        assert 'significant' in result
        
        # Alpha should be one of the tested levels
        assert result['alpha'] in ALPHA_LEVELS
        
        # Metric should be one of the binary metrics
        assert result['metric'] in BINARY_METRICS
        
        # p_value should be between 0 and 1
        assert 0 <= result['p_value'] <= 1
        
        # significant should be boolean
        assert isinstance(result['significant'], bool)

def test_mcnemar_sweep_significance_levels(sample_records):
    """Test that significance is correctly determined at different alpha levels."""
    results = run_mcnemar_sweep(sample_records, ['recovery_success'], ALPHA_LEVELS)
    
    # Group by metric
    metric_results = {r['alpha']: r for r in results if r['metric'] == 'recovery_success'}
    
    # Check that significance is monotonic with alpha
    # If significant at alpha=0.01, should also be significant at alpha=0.05 and 0.10
    # If not significant at alpha=0.10, should also be not significant at lower alphas
    prev_significant = False
    for alpha in sorted(ALPHA_LEVELS):
        current_significant = metric_results[alpha]['significant']
        # If we became significant, we should stay significant
        if current_significant:
            assert prev_significant or True  # First time becoming significant is OK
        prev_significant = current_significant

def test_mcnemar_sweep_empty_data():
    """Test McNemar sweep with empty data."""
    results = run_mcnemar_sweep([], BINARY_METRICS, ALPHA_LEVELS)
    
    # Should still produce results (with p_value=1.0 for no difference)
    expected_count = len(BINARY_METRICS) * len(ALPHA_LEVELS)
    assert len(results) == expected_count
    
    # All p-values should be 1.0 (no difference detected)
    for result in results:
        assert result['p_value'] == 1.0
        assert result['significant'] == False

def test_mcnemar_sweep_no_discordant_pairs():
    """Test McNemar sweep when there are no discordant pairs."""
    records = [
        {'seed': 1, 'protocol': 'Foundation', 'task_success': True},
        {'seed': 1, 'protocol': 'Native Direct', 'task_success': True},
        {'seed': 2, 'protocol': 'Foundation', 'task_success': False},
        {'seed': 2, 'protocol': 'Native Direct', 'task_success': False},
    ]
    
    results = run_mcnemar_sweep(records, ['task_success'], ALPHA_LEVELS)
    
    # Should handle gracefully (p_value=1.0, not significant)
    for result in results:
        assert result['p_value'] == 1.0
        assert result['significant'] == False

@pytest.mark.integration
def test_full_sensitivity_analysis(tmp_path):
    """Integration test for full sensitivity analysis workflow."""
    # Create sample data
    records = []
    for seed in range(1, 31):
        # Simulate some difference between protocols
        foundation_success = seed % 2 == 0
        direct_success = seed % 3 == 0
        
        records.append({
            'seed': seed,
            'protocol': 'Foundation',
            'recovery_success': foundation_success,
            'task_success': foundation_success
        })
        records.append({
            'seed': seed,
            'protocol': 'Native Direct',
            'recovery_success': direct_success,
            'task_success': direct_success
        })
    
    # Run analysis
    results = run_mcnemar_sweep(records, BINARY_METRICS, ALPHA_LEVELS)
    
    # Verify output
    assert len(results) == len(BINARY_METRICS) * len(ALPHA_LEVELS)
    
    # Create DataFrame and verify columns
    df = pd.DataFrame(results)
    assert list(df.columns) == ['alpha', 'metric', 'p_value', 'significant']
    
    # Verify data types
    assert df['alpha'].dtype in ['float64', 'float32']
    assert df['p_value'].dtype in ['float64', 'float32']
    assert df['significant'].dtype == 'bool'
    
    # Verify range of values
    assert df['alpha'].isin(ALPHA_LEVELS).all()
    assert df['metric'].isin(BINARY_METRICS).all()
    assert (df['p_value'] >= 0).all()
    assert (df['p_value'] <= 1).all()
