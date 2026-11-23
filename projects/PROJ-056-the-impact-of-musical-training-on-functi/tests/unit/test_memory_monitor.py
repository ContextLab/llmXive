"""
Unit tests for memory_monitor.py (T005, T005b).
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.memory_monitor import (
    MemoryLimitExceeded,
    check_and_subset_memory,
    check_and_subset_memory_fallback,
    estimate_dataframe_memory_mb,
    simulate_large_memory_usage,
    cleanup_large_memory
)

def test_subset_memory_reduces_usage():
    """Test that subsetting actually reduces memory usage."""
    # Create a large DataFrame
    n_rows = 100000
    df = pd.DataFrame({
        'id': range(n_rows),
        'value': np.random.rand(n_rows),
        'category': np.random.choice(['A', 'B', 'C'], n_rows)
    })
    
    # Estimate memory
    initial_mem = estimate_dataframe_memory_mb(df)
    
    # Subset to a smaller limit (e.g., 10 MB)
    subset_df = check_and_subset_memory(df, limit_gb=0.01) # 10 MB
    
    subset_mem = estimate_dataframe_memory_mb(subset_df)
    
    assert subset_mem <= 10.0, f"Subset memory {subset_mem:.2f} MB exceeds 10 MB limit"
    assert len(subset_df) < len(df), "Subset should have fewer rows"

def test_subset_memory_preserves_structure():
    """Test that subsetting preserves DataFrame structure and types."""
    df = pd.DataFrame({
        'id': range(1000),
        'value': np.random.rand(1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000),
        'group': np.random.choice(['musician', 'non_musician'], 1000)
    })
    
    subset_df = check_and_subset_memory(df, limit_gb=7.0)
    
    assert set(df.columns) == set(subset_df.columns), "Columns should match"
    assert df.dtypes.equals(subset_df.dtypes), "Dtypes should match"

def test_subset_memory_stratified_sampling():
    """Test that stratified sampling is used when 'group' column exists."""
    # Create imbalanced groups
    df = pd.DataFrame({
        'id': range(1000),
        'value': np.random.rand(1000),
        'group': ['musician'] * 900 + ['non_musician'] * 100
    })
    
    subset_df = check_and_subset_memory(df, limit_gb=0.01)
    
    # Check that both groups are present
    assert 'musician' in subset_df['group'].values, "Musician group should be present"
    assert 'non_musician' in subset_df['group'].values, "Non-musician group should be present"
    
    # Check relative proportions are roughly maintained
    original_ratio = df['group'].value_counts()['musician'] / df['group'].value_counts()['non_musician']
    subset_ratio = subset_df['group'].value_counts()['musician'] / subset_df['group'].value_counts()['non_musician']
    
    # Allow some variance due to random sampling
    assert abs(original_ratio - subset_ratio) < 1.0, "Relative proportions should be roughly maintained"

def test_memory_limit_exceeded_impossible_subset():
    """Test that MemoryLimitExceeded is raised when subsetting is impossible."""
    # Create a DataFrame where even a single row exceeds the limit
    # This is hard to simulate with real data, so we test the logic
    # by creating a DataFrame and setting a very low limit
    df = pd.DataFrame({
        'id': [1],
        'value': [1.0],
        'group': ['A']
    })
    
    # This should raise because we can't go below 1 row
    with pytest.raises(MemoryLimitExceeded) as exc_info:
        check_and_subset_memory(df, limit_gb=0.0000001) # Extremely low limit
    
    assert "subsetting impossible" in str(exc_info.value).lower()

def test_fallback_failure_handling():
    """Test T005b fallback failure handling."""
    df = pd.DataFrame({
        'id': [1],
        'value': [1.0],
        'group': ['A']
    })
    
    with pytest.raises(MemoryLimitExceeded) as exc_info:
        check_and_subset_memory_fallback(df, limit_gb=0.0000001)
    
    assert "Memory limit exceeded and subsetting impossible" in str(exc_info.value)

def test_no_subset_needed():
    """Test that original DataFrame is returned if it fits within limit."""
    df = pd.DataFrame({
        'id': range(100),
        'value': np.random.rand(100)
    })
    
    original_mem = estimate_dataframe_memory_mb(df)
    
    # Use a high limit
    result_df = check_and_subset_memory(df, limit_gb=100.0)
    
    assert result_df is df or result_df.equals(df), "Original DataFrame should be returned"

def test_cleanup_large_memory():
    """Test that cleanup function runs without error."""
    # Simulate some memory usage
    simulate_large_memory_usage(10)
    
    # Cleanup
    cleanup_large_memory()
    
    # Should not raise
    assert True

def test_memory_estimate_accuracy():
    """Test that memory estimation is reasonable."""
    df = pd.DataFrame({
        'id': range(10000),
        'value': np.random.rand(10000)
    })
    
    estimated = estimate_dataframe_memory_mb(df)
    # Just check it's a positive number
    assert estimated > 0
    # Check it's within a reasonable range (should be < 10 MB for this small df)
    assert estimated < 10.0