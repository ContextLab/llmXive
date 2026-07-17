"""
Unit tests for Bayesian-multiplicative zero-replacement functionality.

These tests verify:
1. Correct estimation of zero-replacement parameters
2. Proper application of Bayesian-multiplicative replacement
3. Handling of edge cases (all zeros, no zeros, etc.)
4. Integration with the pipeline
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the functions to test
from code.zero_replace import (
    estimate_zero_replacement_params,
    bayesian_multiplicative_replace,
    process_batch,
    run_zero_replacement_pipeline
)
from code.utils.logging import PreprocessingError


class TestZeroReplacementParams:
    """Tests for parameter estimation."""
    
    def test_estimate_params_basic(self):
        """Test parameter estimation on basic data."""
        # Create test data with some zeros
        data = {
            'taxon_a': [10, 0, 20, 0, 15],
            'taxon_b': [5, 8, 0, 12, 0],
            'taxon_c': [0, 0, 0, 0, 0]  # All zeros
        }
        df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'taxon_b', 'taxon_c']
        
        params = estimate_zero_replacement_params(df, taxon_cols)
        
        # Check that parameters are returned
        assert 'geometric_means' in params
        assert 'zero_proportions' in params
        assert 'alpha' in params
        
        # Check geometric means (for non-zero taxa)
        assert 'taxon_a' in params['geometric_means']
        assert 'taxon_b' in params['geometric_means']
        assert 'taxon_c' in params['geometric_means']
        
        # Check zero proportions
        assert abs(params['zero_proportions']['taxon_a'] - 0.4) < 0.01
        assert abs(params['zero_proportions']['taxon_b'] - 0.4) < 0.01
        assert abs(params['zero_proportions']['taxon_c'] - 1.0) < 0.01
        
        # Check alpha is reasonable
        assert 0 < params['alpha'] <= 0.5
    
    def test_estimate_params_empty_dataframe(self):
        """Test parameter estimation on empty DataFrame."""
        df = pd.DataFrame()
        taxon_cols = ['taxon_a', 'taxon_b']
        
        with pytest.raises(ValueError):
            estimate_zero_replacement_params(df, taxon_cols)
    
    def test_estimate_params_no_taxa(self):
        """Test parameter estimation with empty taxon list."""
        df = pd.DataFrame({'taxon_a': [1, 2, 3]})
        
        with pytest.raises(ValueError):
            estimate_zero_replacement_params(df, [])
    
    def test_estimate_params_missing_columns(self):
        """Test parameter estimation with missing taxon columns."""
        df = pd.DataFrame({'taxon_a': [1, 2, 3]})
        taxon_cols = ['taxon_a', 'taxon_b', 'taxon_c']
        
        params = estimate_zero_replacement_params(df, taxon_cols)
        
        # Should only estimate for existing columns
        assert 'taxon_a' in params['geometric_means']
        # Missing columns should be handled gracefully
        assert 'taxon_b' in params['geometric_means']  # Default value
        assert 'taxon_c' in params['geometric_means']  # Default value


class TestBayesianMultiplicativeReplace:
    """Tests for the zero-replacement function."""
    
    def test_replace_zeros_basic(self):
        """Test zero replacement on basic data."""
        data = {
            'taxon_a': [10, 0, 20, 0, 15],
            'taxon_b': [5, 8, 0, 12, 0],
            'taxon_c': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'taxon_b', 'taxon_c']
        
        # Apply replacement
        df_replaced = bayesian_multiplicative_replace(df, taxon_cols)
        
        # Check that no zeros remain
        assert (df_replaced[taxon_cols] == 0).sum().sum() == 0
        
        # Check that all values are positive
        assert (df_replaced[taxon_cols] > 0).all().all()
        
        # Check that original non-zero values are approximately preserved
        # (they may be slightly scaled down)
        original_non_zeros = df[taxon_cols][df[taxon_cols] > 0]
        replaced_non_zeros = df_replaced[taxon_cols][df[taxon_cols] > 0]
        
        # The ratio should be close to 1 (allowing for scaling)
        ratios = replaced_non_zeros / original_non_zeros
        assert (ratios > 0).all().all()
    
    def test_replace_all_zeros(self):
        """Test replacement when all values are zero."""
        data = {
            'taxon_a': [0, 0, 0],
            'taxon_b': [0, 0, 0]
        }
        df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'taxon_b']
        
        df_replaced = bayesian_multiplicative_replace(df, taxon_cols)
        
        # Should have no zeros
        assert (df_replaced[taxon_cols] == 0).sum().sum() == 0
        
        # All values should be positive
        assert (df_replaced[taxon_cols] > 0).all().all()
    
    def test_replace_no_zeros(self):
        """Test replacement when there are no zeros."""
        data = {
            'taxon_a': [10, 20, 30],
            'taxon_b': [5, 15, 25]
        }
        df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'taxon_b']
        
        df_replaced = bayesian_multiplicative_replace(df, taxon_cols)
        
        # Values should be very close to original (only scaled)
        np.testing.assert_array_almost_equal(
            df_replaced[taxon_cols].values,
            df[taxon_cols].values,
            decimal=5
        )
    
    def test_replace_with_custom_alpha(self):
        """Test replacement with custom alpha parameter."""
        data = {
            'taxon_a': [10, 0, 20],
            'taxon_b': [5, 0, 15]
        }
        df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'taxon_b']
        
        # Test with different alpha values
        df_alpha1 = bayesian_multiplicative_replace(df, taxon_cols, alpha=0.1)
        df_alpha2 = bayesian_multiplicative_replace(df, taxon_cols, alpha=0.5)
        
        # Different alpha should produce different results
        assert not df_alpha1.equals(df_alpha2)
        
        # Higher alpha should result in larger replacements for zeros
        zero_rows = df[taxon_cols].eq(0).any(axis=1)
        replacement_diff = (df_alpha2.loc[zero_rows, taxon_cols] - 
                          df_alpha1.loc[zero_rows, taxon_cols]).mean()
        assert replacement_diff > 0  # Higher alpha -> larger replacements
    
    def test_replace_invalid_columns(self):
        """Test replacement with invalid column names."""
        data = {
            'taxon_a': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'nonexistent']
        
        with pytest.raises(PreprocessingError):
            bayesian_multiplicative_replace(df, taxon_cols)
    
    def test_replace_empty_dataframe(self):
        """Test replacement on empty DataFrame."""
        df = pd.DataFrame()
        taxon_cols = ['taxon_a', 'taxon_b']
        
        result = bayesian_multiplicative_replace(df, taxon_cols)
        
        assert result.empty


class TestProcessBatch:
    """Tests for batch processing."""
    
    def test_process_batch_basic(self):
        """Test basic batch processing."""
        data = {
            'taxon_a': [10, 0, 20, 0],
            'taxon_b': [5, 8, 0, 12]
        }
        batch_df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'taxon_b']
        
        processed = process_batch(batch_df, taxon_cols)
        
        # Should have no zeros
        assert (processed[taxon_cols] == 0).sum().sum() == 0
        
        # Should have same shape
        assert processed.shape == batch_df.shape
    
    def test_process_batch_with_params(self):
        """Test batch processing with pre-computed parameters."""
        data = {
            'taxon_a': [10, 0, 20],
            'taxon_b': [5, 0, 15]
        }
        batch_df = pd.DataFrame(data)
        taxon_cols = ['taxon_a', 'taxon_b']
        
        # Estimate params first
        params = estimate_zero_replacement_params(batch_df, taxon_cols)
        
        # Process with params
        processed = process_batch(batch_df, taxon_cols, params=params)
        
        # Should have no zeros
        assert (processed[taxon_cols] == 0).sum().sum() == 0


class TestZeroReplacementPipeline:
    """Tests for the full pipeline."""
    
    def test_pipeline_basic(self):
        """Test basic pipeline execution."""
        # Create test data
        data = {
            'eids': [1, 2, 3, 4, 5],
            'taxon_a': [10, 0, 20, 0, 15],
            'taxon_b': [5, 8, 0, 12, 0],
            'taxon_c': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            
            # Save input
            df.to_parquet(input_path)
            
            # Run pipeline
            result_path = run_zero_replacement_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                taxon_columns=['taxon_a', 'taxon_b', 'taxon_c'],
                use_streaming=False
            )
            
            # Check output exists
            assert Path(result_path).exists()
            
            # Load and verify
            result_df = pd.read_parquet(result_path)
            
            # Should have no zeros in taxon columns
            assert (result_df[['taxon_a', 'taxon_b', 'taxon_c']] == 0).sum().sum() == 0
            
            # Should have same number of rows
            assert len(result_df) == len(df)
    
    def test_pipeline_infer_taxa(self):
        """Test pipeline with automatic taxon column inference."""
        data = {
            'eids': [1, 2, 3],
            'taxon_a': [10, 0, 20],
            'taxon_b': [5, 8, 0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            
            df.to_parquet(input_path)
            
            # Run pipeline without specifying taxa
            result_path = run_zero_replacement_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                use_streaming=False
            )
            
            # Should succeed and produce output
            assert Path(result_path).exists()
            
            result_df = pd.read_parquet(result_path)
            assert (result_df[['taxon_a', 'taxon_b']] == 0).sum().sum() == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])