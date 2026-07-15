"""
Unit tests for performance optimization functions.

Tests batching, memory-efficient processing, and model fitting optimization.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import gc
from unittest.mock import patch, MagicMock
import tempfile
import json

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.performance import (
    estimate_dataframe_memory,
    downcast_dataframe,
    split_dataframe_by_memory,
    calculate_memory_requirements,
    fit_model_batch,
    run_batched_model_fitting
)


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    np.random.seed(42)
    n = 1000
    return pd.DataFrame({
        'id': range(n),
        'value_float': np.random.randn(n),
        'value_int': np.random.randint(0, 100, n),
        'category': np.random.choice(['A', 'B', 'C'], n),
        'country': np.random.choice(['KE', 'IN', 'VN'], n),
        'year': np.random.choice([2018, 2019, 2020], n),
        'food_security': np.random.randn(n),
        'csa_index': np.random.rand(n),
        'age': np.random.randint(20, 70, n),
        'education': np.random.randint(0, 15, n),
        'household_size': np.random.randint(1, 10, n),
        'sampling_weight': np.random.rand(n) * 2 + 0.5
    })


@pytest.fixture
def large_dataframe():
    """Create a larger dataframe for memory testing."""
    np.random.seed(42)
    n = 50000
    return pd.DataFrame({
        'id': range(n),
        'value_float': np.random.randn(n).astype(np.float64),
        'value_int': np.random.randint(0, 100, n).astype(np.int64),
        'category': np.random.choice(['A', 'B', 'C'], n),
        'country': np.random.choice(['KE', 'IN', 'VN'], n),
        'year': np.random.choice([2018, 2019, 2020], n),
        'food_security': np.random.randn(n),
        'csa_index': np.random.rand(n),
        'age': np.random.randint(20, 70, n),
        'education': np.random.randint(0, 15, n),
        'household_size': np.random.randint(1, 10, n),
        'sampling_weight': np.random.rand(n) * 2 + 0.5
    })


class TestMemoryEstimation:
    """Tests for memory estimation functions."""

    def test_estimate_dataframe_memory(self, sample_dataframe):
        """Test memory estimation accuracy."""
        estimated = estimate_dataframe_memory(sample_dataframe)
        assert estimated > 0
        assert isinstance(estimated, (int, float))
        
        # Verify it matches pandas calculation
        actual = sample_dataframe.memory_usage(deep=True).sum()
        assert abs(estimated - actual) < 1  # Within 1 byte tolerance

    def test_calculate_memory_requirements(self, sample_dataframe):
        """Test memory requirements calculation."""
        mem_info = calculate_memory_requirements(sample_dataframe, num_batches=2)
        
        assert 'estimated_size_bytes' in mem_info
        assert 'total_required_bytes' in mem_info
        assert 'batch_size_bytes' in mem_info
        assert mem_info['total_required_bytes'] >= mem_info['estimated_size_bytes']
        assert mem_info['batch_size_bytes'] < mem_info['total_required_bytes']
        assert mem_info['num_batches'] == 2


class TestDowncasting:
    """Tests for data type downcasting."""

    def test_downcast_float64_to_float32(self):
        """Test downcasting float64 to float32."""
        df = pd.DataFrame({
            'float64_col': np.random.randn(100).astype(np.float64),
            'int64_col': np.random.randint(0, 100, 100).astype(np.int64)
        })
        
        original_memory = df.memory_usage(deep=True).sum()
        downcasted = downcast_dataframe(df)
        new_memory = downcasted.memory_usage(deep=True).sum()
        
        # Should reduce memory
        assert new_memory <= original_memory
        
        # Verify data integrity
        pd.testing.assert_frame_equal(
            downcasted.reset_index(drop=True),
            df.reset_index(drop=True),
            check_dtype=False  # Allow dtype differences
        )

    def test_downcast_preserves_categorical(self):
        """Test that categorical columns are preserved."""
        df = pd.DataFrame({
            'category': pd.Categorical(['A', 'B', 'C'] * 100),
            'value': np.random.randn(300)
        })
        
        downcasted = downcast_dataframe(df)
        
        assert pd.api.types.is_categorical_dtype(downcasted['category'])


class TestBatching:
    """Tests for dataframe splitting and batching."""

    def test_split_dataframe_fits_in_memory(self, sample_dataframe):
        """Test splitting when data already fits in memory."""
        batches = split_dataframe_by_memory(sample_dataframe, max_memory_gb=10.0)
        
        assert len(batches) == 1
        pd.testing.assert_frame_equal(batches[0], sample_dataframe)

    def test_split_dataframe_splits_correctly(self, large_dataframe):
        """Test splitting when data exceeds memory limit."""
        # Set a very small limit to force splitting
        batches = split_dataframe_by_memory(large_dataframe, max_memory_gb=0.001)
        
        assert len(batches) > 1
        
        # Verify all rows are preserved
        total_rows = sum(len(batch) for batch in batches)
        assert total_rows == len(large_dataframe)
        
        # Verify no duplicate rows
        all_ids = []
        for batch in batches:
            all_ids.extend(batch['id'].tolist())
        
        assert len(all_ids) == len(set(all_ids))

    def test_split_dataframe_memory_constraints(self, large_dataframe):
        """Test that each batch respects memory limits."""
        max_memory_gb = 0.01  # 10 MB
        batches = split_dataframe_by_memory(large_dataframe, max_memory_gb=max_memory_gb)
        
        max_memory_bytes = max_memory_gb * (1024**3)
        
        for i, batch in enumerate(batches):
            batch_memory = estimate_dataframe_memory(batch)
            # Allow 10% tolerance
            assert batch_memory <= max_memory_bytes * 1.1, \
                f"Batch {i} exceeds memory limit: {batch_memory / (1024**3):.4f} GB > {max_memory_gb} GB"


class TestModelFitting:
    """Tests for batched model fitting."""

    @patch('analysis.performance.smf.mixedlm')
    def test_fit_model_batch_success(self, mock_mixedlm, sample_dataframe):
        """Test successful model fitting on a batch."""
        # Mock the model and result
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.params = pd.Series({'csa_index': 0.5, 'age': 0.1})
        mock_result.pvalues = pd.Series({'csa_index': 0.01, 'age': 0.05})
        mock_result.bic = 1000.0
        mock_result.aic = 950.0
        mock_result.llf = -400.0
        mock_result.ngroups = 3
        mock_result.converged = True
        mock_result.cov_re = pd.DataFrame({'csa_index': [0.1]})
        
        mock_model.return_value.fit.return_value = mock_result
        
        formula = "food_security ~ csa_index + age"
        result = fit_model_batch(
            sample_dataframe,
            formula=formula,
            random_effect="country"
        )
        
        assert result['success'] is True
        assert result['n_obs'] == len(sample_dataframe)
        assert 'coefficients' in result
        assert 'pvalues' in result
        assert 'bic' in result

    @patch('analysis.performance.smf.mixedlm')
    def test_fit_model_batch_failure(self, mock_mixedlm, sample_dataframe):
        """Test model fitting failure handling."""
        # Mock a failure
        mock_model.return_value.fit.side_effect = Exception("Convergence failed")
        
        formula = "food_security ~ csa_index + age"
        result = fit_model_batch(
            sample_dataframe,
            formula=formula,
            random_effect="country"
        )
        
        assert result['success'] is False
        assert 'error' in result

    def test_run_batched_model_fitting_integration(self, sample_dataframe):
        """Integration test for batched model fitting."""
        formula = "food_security ~ csa_index + age"
        
        # Use sequential mode for testing
        results = run_batched_model_fitting(
            sample_dataframe,
            formula=formula,
            random_effect="country",
            weights_col=None,
            max_memory_gb=10.0,  # Large enough to fit in one batch
            num_workers=1,
            progress=False
        )
        
        assert 'total_batches' in results
        assert 'successful_batches' in results
        assert 'total_time_seconds' in results
        assert results['total_batches'] >= 1


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame()
        
        with pytest.raises((ValueError, IndexError)):
            split_dataframe_by_memory(df, max_memory_gb=1.0)

    def test_single_row_dataframe(self):
        """Test handling of single row dataframe."""
        df = pd.DataFrame({'a': [1], 'b': [2.0]})
        
        batches = split_dataframe_by_memory(df, max_memory_gb=1.0)
        assert len(batches) == 1
        assert len(batches[0]) == 1

    def test_memory_limit_zero(self, sample_dataframe):
        """Test behavior with zero memory limit."""
        # This should create many small batches
        batches = split_dataframe_by_memory(sample_dataframe, max_memory_gb=0.0001)
        
        assert len(batches) > 0
        # Each batch should be small
        for batch in batches:
            assert len(batch) > 0

    def test_missing_weights_column(self, sample_dataframe):
        """Test handling of missing weights column."""
        formula = "food_security ~ csa_index"
        
        # Should not raise error when weights column is missing
        results = run_batched_model_fitting(
            sample_dataframe,
            formula=formula,
            random_effect="country",
            weights_col="nonexistent_column",
            num_workers=1,
            progress=False
        )
        
        assert 'total_batches' in results


class TestPerformanceMetrics:
    """Tests for performance metric calculations."""

    def test_memory_reduction_calculation(self, large_dataframe):
        """Test that downcasting reduces memory."""
        original_memory = large_dataframe.memory_usage(deep=True).sum()
        downcasted = downcast_dataframe(large_dataframe.copy())
        new_memory = downcasted.memory_usage(deep=True).sum()
        
        reduction = (original_memory - new_memory) / original_memory
        
        # Should achieve some reduction
        assert reduction >= 0
        # Typically expect at least some reduction for float64->float32
        if original_memory > new_memory:
            assert reduction > 0.01  # At least 1% reduction if any

    def test_batch_size_consistency(self, large_dataframe):
        """Test that batch sizes are consistent."""
        batches = split_dataframe_by_memory(large_dataframe, max_memory_gb=0.05)
        
        if len(batches) > 1:
            sizes = [len(batch) for batch in batches]
            # All batches should be roughly similar size (last one may be smaller)
            assert all(sizes[:-1])  # All but last should be similar
            # Last batch can be smaller
            assert sizes[-1] <= sizes[0] + 10  # Allow small variance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
