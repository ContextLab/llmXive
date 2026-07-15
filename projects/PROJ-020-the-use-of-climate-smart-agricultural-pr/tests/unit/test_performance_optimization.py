"""
Unit tests for performance optimization module.

Tests batching, memory efficiency, and model fitting optimization.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis.performance import (
    estimate_dataframe_memory,
    downcast_dataframe,
    split_dataframe_by_memory,
    fit_model_batch,
    calculate_memory_requirements,
    BATCH_SIZE_DEFAULT,
    MAX_BATCH_MEMORY_GB
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    n_rows = 1000
    
    df = pd.DataFrame({
        'id': range(n_rows),
        'value_float': np.random.randn(n_rows),
        'value_int': np.random.randint(0, 100, n_rows),
        'category': np.random.choice(['A', 'B', 'C'], n_rows),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_rows),
        'outcome': np.random.randn(n_rows)
    })
    
    return df


@pytest.fixture
def large_dataframe():
    """Create a larger DataFrame to test memory splitting."""
    np.random.seed(42)
    n_rows = 50000
    
    df = pd.DataFrame({
        'id': range(n_rows),
        'value_float': np.random.randn(n_rows),
        'value_int': np.random.randint(0, 100, n_rows),
        'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], n_rows),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_rows),
        'outcome': np.random.randn(n_rows)
    })
    
    return df


class TestMemoryEstimation:
    """Tests for memory estimation functions."""
    
    def test_estimate_dataframe_memory_positive(self, sample_dataframe):
        """Test that memory estimation returns positive values."""
        memory_gb = estimate_dataframe_memory(sample_dataframe)
        assert memory_gb > 0, "Memory estimate should be positive"
        assert isinstance(memory_gb, float), "Memory estimate should be float"
    
    def test_memory_scaling(self, sample_dataframe):
        """Test that memory scales with DataFrame size."""
        memory_original = estimate_dataframe_memory(sample_dataframe)
        
        # Double the DataFrame
        df_doubled = pd.concat([sample_dataframe, sample_dataframe], ignore_index=True)
        memory_doubled = estimate_dataframe_memory(df_doubled)
        
        # Memory should approximately double
        assert memory_doubled > memory_original * 0.9, "Memory should scale with size"
        assert memory_doubled < memory_original * 1.1, "Memory should scale proportionally"


class TestMemoryOptimization:
    """Tests for memory optimization functions."""
    
    def test_downcast_reduces_memory(self, sample_dataframe):
        """Test that downcasting reduces memory usage."""
        original_memory = estimate_dataframe_memory(sample_dataframe)
        optimized_df = downcast_dataframe(sample_dataframe)
        optimized_memory = estimate_dataframe_memory(optimized_df)
        
        # Optimized memory should be less than or equal to original
        assert optimized_memory <= original_memory, "Downcasting should reduce or maintain memory"
    
    def test_downcast_preserves_data(self, sample_dataframe):
        """Test that downcasting preserves data values."""
        optimized_df = downcast_dataframe(sample_dataframe)
        
        # Check that numeric values are preserved
        assert np.allclose(
            sample_dataframe['value_float'].values,
            optimized_df['value_float'].values,
            rtol=1e-5
        )
        assert np.array_equal(
            sample_dataframe['value_int'].values,
            optimized_df['value_int'].values
        )
    
    def test_downcast_preserves_categories(self, sample_dataframe):
        """Test that downcasting preserves categorical data."""
        optimized_df = downcast_dataframe(sample_dataframe)
        
        assert list(sample_dataframe['category'].values) == list(optimized_df['category'].values)
        assert list(sample_dataframe['region'].values) == list(optimized_df['region'].values)

class TestBatching:
    """Tests for DataFrame batching functions."""
    
    def test_split_returns_list(self, sample_dataframe):
        """Test that split function returns a list."""
        chunks = split_dataframe_by_memory(sample_dataframe, max_memory_gb=10.0)
        assert isinstance(chunks, list), "Should return a list"
        assert len(chunks) >= 1, "Should have at least one chunk"
    
    def test_split_preserves_total_rows(self, sample_dataframe):
        """Test that splitting preserves total row count."""
        total_rows = len(sample_dataframe)
        chunks = split_dataframe_by_memory(sample_dataframe, max_memory_gb=10.0)
        
        chunk_rows = sum(len(chunk) for chunk in chunks)
        assert chunk_rows == total_rows, "Total rows should be preserved"
    
    def test_split_respects_memory_limit(self, large_dataframe):
        """Test that chunks respect memory limits."""
        max_memory = 0.1  # Very small limit to force splitting
        chunks = split_dataframe_by_memory(large_dataframe, max_memory_gb=max_memory)
        
        for chunk in chunks:
            chunk_memory = estimate_dataframe_memory(chunk)
            assert chunk_memory <= max_memory * 1.1, f"Chunk memory {chunk_memory} exceeds limit {max_memory}"
    
    def test_split_empty_dataframe(self):
        """Test splitting an empty DataFrame."""
        df = pd.DataFrame({'a': [], 'b': []})
        chunks = split_dataframe_by_memory(df, max_memory_gb=1.0)
        
        assert len(chunks) == 1, "Empty DataFrame should return one empty chunk"
        assert len(chunks[0]) == 0, "Chunk should be empty"

class TestModelFitting:
    """Tests for model fitting functions."""
    
    def test_fit_model_batch_success(self, sample_dataframe):
        """Test successful model fitting on a batch."""
        formula = "outcome ~ value_float + value_int"
        group_col = "region"
        
        result = fit_model_batch(
            batch_data=sample_dataframe,
            formula=formula,
            group_col=group_col,
            batch_id=0
        )
        
        assert result['success'], "Model fitting should succeed"
        assert result['coefficients'] is not None, "Coefficients should be present"
        assert result['pvalues'] is not None, "P-values should be present"
        assert result['n_obs'] == len(sample_dataframe), "Row count should match"
    
    def test_fit_model_batch_insufficient_data(self):
        """Test fitting with insufficient data."""
        df = pd.DataFrame({
            'outcome': [1.0],
            'value': [1.0],
            'group': ['A']
        })
        
        result = fit_model_batch(
            batch_data=df,
            formula="outcome ~ value",
            group_col="group",
            batch_id=0
        )
        
        assert not result['success'], "Should fail with insufficient data"
        assert "Insufficient" in result['error']
    
    def test_fit_model_batch_insufficient_groups(self):
        """Test fitting with insufficient groups."""
        df = pd.DataFrame({
            'outcome': [1.0, 2.0, 3.0],
            'value': [1.0, 2.0, 3.0],
            'group': ['A', 'A', 'A']  # Only one group
        })
        
        result = fit_model_batch(
            batch_data=df,
            formula="outcome ~ value",
            group_col="group",
            batch_id=0
        )
        
        assert not result['success'], "Should fail with insufficient groups"
        assert "Insufficient groups" in result['error']
    
    def test_fit_model_batch_timeout(self, sample_dataframe):
        """Test model fitting with timeout."""
        formula = "outcome ~ value_float"
        group_col = "region"
        
        # Very short timeout should cause failure or success depending on speed
        result = fit_model_batch(
            batch_data=sample_dataframe,
            formula=formula,
            group_col=group_col,
            batch_id=0,
            timeout_seconds=1
        )
        
        # Result should be complete (either success or timeout error)
        assert 'success' in result
        assert 'fit_time' in result
        assert result['fit_time'] <= 2.0, "Should respect timeout"

class TestMemoryRequirements:
    """Tests for memory requirement calculation."""
    
    def test_calculate_memory_requirements_positive(self, sample_dataframe):
        """Test that memory requirements are positive."""
        formula = "outcome ~ value_float + value_int"
        mem_reqs = calculate_memory_requirements(sample_dataframe, formula)
        
        assert mem_reqs['data_memory_gb'] > 0
        assert mem_reqs['total_estimated_memory_gb'] > 0
        assert mem_reqs['recommended_batch_size_gb'] > 0
    
    def test_memory_requirements_formula_complexity(self, sample_dataframe):
        """Test that complex formulas increase memory estimate."""
        simple_formula = "outcome ~ value_float"
        complex_formula = "outcome ~ value_float + value_int + category + region"
        
        simple_reqs = calculate_memory_requirements(sample_dataframe, simple_formula)
        complex_reqs = calculate_memory_requirements(sample_dataframe, complex_formula)
        
        assert complex_reqs['estimated_model_memory_gb'] > simple_reqs['estimated_model_memory_gb']

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_dataframe_memory(self):
        """Test memory estimation on empty DataFrame."""
        df = pd.DataFrame()
        memory = estimate_dataframe_memory(df)
        assert memory == 0.0, "Empty DataFrame should have zero memory"
    
    def test_single_row_batch(self):
        """Test fitting on single row."""
        df = pd.DataFrame({
            'outcome': [1.0],
            'value': [1.0],
            'group': ['A']
        })
        
        result = fit_model_batch(df, "outcome ~ value", "group", 0)
        assert not result['success'], "Single row should fail"
    
    def test_all_nan_values(self):
        """Test fitting with all NaN values."""
        df = pd.DataFrame({
            'outcome': [np.nan, np.nan, np.nan],
            'value': [np.nan, np.nan, np.nan],
            'group': ['A', 'B', 'C']
        })
        
        result = fit_model_batch(df, "outcome ~ value", "group", 0)
        # Should fail gracefully
        assert not result['success'] or result['error'] is not None
    
    def test_categorical_only_data(self):
        """Test fitting with only categorical predictors."""
        df = pd.DataFrame({
            'outcome': [1.0, 2.0, 3.0, 4.0],
            'category': ['A', 'B', 'A', 'B'],
            'group': ['X', 'X', 'Y', 'Y']
        })
        
        result = fit_model_batch(df, "outcome ~ category", "group", 0)
        # Should succeed if there's enough variation
        assert result['success'] or "Insufficient" in (result.get('error') or "")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])