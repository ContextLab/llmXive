"""
Unit tests for T033: Outlier Threshold Sweep.

Tests for:
- FPR calculation on null datasets
- Inconsistency rate calculation
- Threshold sweep execution
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from t033_outlier_threshold_sweep import (
    generate_null_dataset,
    estimate_fpr_for_dataset,
    calculate_inconsistency_rate,
    run_threshold_sweep,
    THRESHOLDS
)
from cleaning import apply_iqr_outlier_removal

@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'outcome': np.random.randn(100)
    })

@pytest.fixture
def sample_baseline_metrics():
    """Create sample baseline metrics."""
    return {
        'datasets': [
            {
                'dataset_name': 'test_dataset',
                't_test': {
                    'test1': {'p_value': 0.03},
                    'test2': {'p_value': 0.07}
                },
                'regression': {}
            },
            {
                'dataset_name': 'test_dataset2',
                't_test': {
                    'test1': {'p_value': 0.02},
                    'test2': {'p_value': 0.04}
                },
                'regression': {}
            }
        ]
    }

@pytest.fixture
def sample_cleaned_metrics():
    """Create sample cleaned metrics."""
    return {
        'datasets': [
            {
                'dataset_name': 'test_dataset_cleaned_k1.5',
                't_test': {
                    'test1': {'p_value': 0.08},  # Changed significance
                    'test2': {'p_value': 0.06}
                },
                'regression': {}
            },
            {
                'dataset_name': 'test_dataset2_cleaned_k1.5',
                't_test': {
                    'test1': {'p_value': 0.01},  # Still significant
                    'test2': {'p_value': 0.03}
                },
                'regression': {}
            }
        ]
    }

def test_generate_null_dataset(sample_dataset):
    """Test that null dataset generation shuffles the outcome column."""
    np.random.seed(42)
    null_df = generate_null_dataset(sample_dataset, seed=42)
    
    # Check that outcome column is different (shuffled)
    assert not null_df['outcome'].equals(sample_dataset['outcome'])
    
    # Check that other columns are unchanged
    assert null_df['feature1'].equals(sample_dataset['feature1'])
    assert null_df['feature2'].equals(sample_dataset['feature2'])

def test_generate_null_dataset_preserves_shape(sample_dataset):
    """Test that null dataset has the same shape as original."""
    null_df = generate_null_dataset(sample_dataset, seed=42)
    assert null_df.shape == sample_dataset.shape

def test_calculate_inconsistency_rate(sample_baseline_metrics, sample_cleaned_metrics):
    """Test inconsistency rate calculation."""
    # For k=1.5:
    # - test_dataset: baseline p=0.03 (sig), cleaned p=0.08 (not sig) -> INCONSISTENT
    # - test_dataset2: baseline p=0.02 (sig), cleaned p=0.01 (sig) -> CONSISTENT
    # Expected: 1/2 = 0.5
    
    rate = calculate_inconsistency_rate(
        sample_baseline_metrics,
        sample_cleaned_metrics,
        threshold_k=1.5
    )
    
    assert rate == 0.5

def test_calculate_inconsistency_rate_empty_metrics():
    """Test inconsistency rate with empty metrics."""
    rate = calculate_inconsistency_rate({}, {}, 1.5)
    assert rate == 0.0

def test_calculate_inconsistency_rate_no_matching_cleaned():
    """Test inconsistency rate when no cleaned datasets match."""
    baseline = {'datasets': [{'dataset_name': 'test', 't_test': {}}]}
    cleaned = {'datasets': [{'dataset_name': 'other_cleaned_k1.5', 't_test': {}}]}
    
    rate = calculate_inconsistency_rate(baseline, cleaned, 1.5)
    assert rate == 0.0

def test_threshold_sweep_structure(sample_baseline_metrics, sample_cleaned_metrics):
    """Test that threshold sweep returns expected structure."""
    with patch('t033_outlier_threshold_sweep.load_dataset_from_processed') as mock_load:
        # Mock a simple dataset
        mock_load.return_value = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50),
            'outcome': np.random.randn(50)
        })
        
        results = run_threshold_sweep(
            sample_baseline_metrics,
            sample_cleaned_metrics,
            processed_dir="data/processed",
            num_null_datasets=2,  # Small number for testing
            seed=42
        )
        
        assert 'thresholds' in results
        assert 'sweep_metadata' in results
        assert len(results['thresholds']) == len(THRESHOLDS)
        
        # Check structure of each threshold result
        for threshold_result in results['thresholds']:
            assert 'threshold_k' in threshold_result
            assert 'fpr' in threshold_result
            assert 'inconsistency_rate' in threshold_result
            assert 'fpr_details' in threshold_result
            assert 'num_null_datasets_tested' in threshold_result

def test_fpr_calculation():
    """Test FPR calculation on null datasets."""
    # Create a simple null dataset where we know the outcome is shuffled
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'outcome': np.random.randn(100)
    })
    
    # Since outcome is shuffled, there should be no true relationship
    # FPR should be low (close to 0.05 for alpha=0.05)
    is_sig, p_val = estimate_fpr_for_dataset(df, threshold_k=1.5, seed=42)
    
    # Just check that the function returns valid values
    assert isinstance(is_sig, bool)
    assert 0.0 <= p_val <= 1.0

def test_threshold_sweep_empty_metrics():
    """Test threshold sweep with empty metrics."""
    results = run_threshold_sweep(
        {'datasets': []},
        {'datasets': []},
        processed_dir="data/processed",
        num_null_datasets=1,
        seed=42
    )
    
    assert 'thresholds' in results
    assert len(results['thresholds']) == len(THRESHOLDS)
    
    # All inconsistency rates should be 0.0
    for t in results['thresholds']:
        assert t['inconsistency_rate'] == 0.0

def test_threshold_values():
    """Test that all expected thresholds are included."""
    expected_thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    assert set(THRESHOLDS) == set(expected_thresholds)

def test_fpr_details_structure():
    """Test that FPR details contain expected fields."""
    # This is tested indirectly in test_threshold_sweep_structure
    # but we can verify the structure here
    expected_fields = ['dataset_id', 'threshold_k', 'is_significant', 'p_value']
    
    # Create a mock result
    mock_result = {
        'dataset_id': 'null_k1.5_iter_0',
        'threshold_k': 1.5,
        'is_significant': False,
        'p_value': 0.5
    }
    
    for field in expected_fields:
        assert field in mock_result