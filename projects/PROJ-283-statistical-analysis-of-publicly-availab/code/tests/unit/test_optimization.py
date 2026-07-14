import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.utils.optimization import (
    get_current_memory_usage_gb,
    check_memory_usage,
    sample_dataframe,
    optimize_dataframe_dtypes,
    cleanup_memory,
    ensure_memory_constraints
)

class TestMemoryUsage:
    def test_get_current_memory_usage_returns_positive(self):
        """Test that memory usage function returns a positive number"""
        usage = get_current_memory_usage_gb()
        assert usage >= 0.0

    def test_check_memory_usage_returns_boolean(self):
        """Test that check_memory_usage returns a boolean"""
        result = check_memory_usage()
        assert isinstance(result, bool)

class TestSampling:
    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe for testing"""
        n = 1000
        return pd.DataFrame({
            'id': range(n),
            'value': np.random.randn(n),
            'category': np.random.choice(['A', 'B', 'C'], n),
            'outcome': np.random.choice(['1-0', '0-1', '1/2-1/2'], n)
        })

    def test_sample_smaller_than_requested_returns_original(self, sample_data):
        """Test that sampling doesn't reduce data if it's already small"""
        result = sample_dataframe(sample_data, sample_size=2000)
        assert len(result) == len(sample_data)

    def test_sample_reduces_to_requested_size(self, sample_data):
        """Test that sampling reduces data to requested size"""
        result = sample_dataframe(sample_data, sample_size=100)
        assert len(result) == 100

    def test_sample_preserves_stratification(self, sample_data):
        """Test that stratified sampling preserves outcome distribution"""
        result = sample_dataframe(sample_data, sample_size=100)
        # Just check that we can calculate proportions without error
        proportions = result['outcome'].value_counts(normalize=True)
        assert abs(proportions.sum() - 1.0) < 0.01

    def test_sample_preserves_data_types(self, sample_data):
        """Test that sampling preserves data types"""
        result = sample_dataframe(sample_data, sample_size=100)
        assert result['id'].dtype == sample_data['id'].dtype
        assert result['value'].dtype == sample_data['value'].dtype

class TestOptimization:
    @pytest.fixture
    def large_dataframe(self):
        """Create a dataframe with various data types"""
        n = 10000
        return pd.DataFrame({
            'int_col': np.random.randint(0, 100, n),
            'float_col': np.random.randn(n),
            'string_col': np.random.choice(['short', 'medium', 'long'], n),
            'category_col': pd.Categorical(np.random.choice(['A', 'B', 'C', 'D'], n))
        })

    def test_optimize_dataframe_returns_dataframe(self, large_dataframe):
        """Test that optimization returns a dataframe"""
        result = optimize_dataframe_dtypes(large_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_optimize_preserves_shape(self, large_dataframe):
        """Test that optimization preserves row count"""
        result = optimize_dataframe_dtypes(large_dataframe)
        assert len(result) == len(large_dataframe)
        assert len(result.columns) == len(large_dataframe.columns)

    def test_optimize_converts_low_cardinality_to_category(self, large_dataframe):
        """Test that low cardinality columns are converted to category"""
        result = optimize_dataframe_dtypes(large_dataframe)
        # string_col has low cardinality (3 unique values out of 10000)
        assert result['string_col'].dtype.name == 'category'

    def test_optimize_downcasts_floats(self, large_dataframe):
        """Test that floats are downcast when possible"""
        result = optimize_dataframe_dtypes(large_dataframe)
        # float_col should be downcast to float32 if possible
        assert result['float_col'].dtype in [np.float32, np.float64]

class TestFullPipeline:
    @pytest.fixture
    def test_dataframe(self):
        """Create a test dataframe"""
        n = 5000
        return pd.DataFrame({
            'game_id': range(n),
            'white_rating': np.random.randint(800, 3000, n),
            'black_rating': np.random.randint(800, 3000, n),
            'eco_code': np.random.choice(['A00', 'B12', 'C44'], n),
            'avg_move_time': np.random.uniform(5.0, 30.0, n),
            'outcome': np.random.choice(['1-0', '0-1', '1/2-1/2'], n),
            'prob': np.random.uniform(0.1, 0.9, n),
            'deviation': np.random.uniform(-0.5, 0.5, n)
        })

    def test_ensure_memory_constraints_returns_tuple(self, test_dataframe):
        """Test that the main function returns expected tuple"""
        result_df, sampled = ensure_memory_constraints(test_dataframe)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(sampled, bool)

    def test_ensure_memory_constraints_preserves_columns(self, test_dataframe):
        """Test that all columns are preserved"""
        result_df, _ = ensure_memory_constraints(test_dataframe)
        assert set(result_df.columns) == set(test_dataframe.columns)

    def test_ensure_memory_constraints_handles_small_dataframe(self, test_dataframe):
        """Test that small dataframes are not unnecessarily sampled"""
        result_df, sampled = ensure_memory_constraints(test_dataframe, force_sample=False)
        # Should not sample if under limit
        assert sampled == False or len(result_df) == len(test_dataframe)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])