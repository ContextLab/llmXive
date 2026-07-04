"""
Unit tests for Bayesian-multiplicative zero-replacement functionality.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

from code.zero_replace import (
    estimate_zero_replacement_params,
    bayesian_multiplicative_replace,
    process_batch,
    run_zero_replacement_pipeline
)
from code.config import get_path

class TestZeroReplacement:
    """Test suite for zero replacement algorithms."""
    
    def test_estimate_zero_replacement_params_basic(self):
        """Test parameter estimation with basic data."""
        # Create test data with some zeros
        data = pd.DataFrame({
            'taxon_A': [10, 0, 20, 0, 15],
            'taxon_B': [0, 5, 0, 8, 12],
            'taxon_C': [3, 4, 5, 6, 7]
        })
        
        params = estimate_zero_replacement_params(data, ['taxon_A', 'taxon_B', 'taxon_C'])
        
        assert 'taxon_A' in params
        assert 'taxon_B' in params
        assert 'taxon_C' in params
        assert all(v > 0 for v in params.values())
        
    def test_bayesian_multiplicative_replace_no_zeros(self):
        """Test replacement when there are no zeros."""
        counts = np.array([[10, 20, 30], [15, 25, 35]])
        concentrations = {'taxon_0': 1.0, 'taxon_1': 1.0, 'taxon_2': 1.0}
        
        result = bayesian_multiplicative_replace(counts, concentrations)
        
        # Should be very close to original (small adjustments for normalization)
        assert np.allclose(result, counts, rtol=1e-5)
        assert (result > 0).all()
        
    def test_bayesian_multiplicative_replace_with_zeros(self):
        """Test replacement with zero values."""
        counts = np.array([[0, 20, 30], [15, 0, 35], [0, 0, 40]])
        concentrations = {'taxon_0': 1.0, 'taxon_1': 1.0, 'taxon_2': 1.0}
        
        result = bayesian_multiplicative_replace(counts, concentrations)
        
        # All values should be positive
        assert (result > 0).all()
        # No original zeros should remain zero
        assert not (result == 0).any()
        # Row sums should be approximately preserved
        original_sums = counts.sum(axis=1)
        result_sums = result.sum(axis=1)
        assert np.allclose(original_sums, result_sums, rtol=0.1)
        
    def test_process_batch_integration(self):
        """Test batch processing with sample data."""
        # Create test batch
        batch = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'taxon_A': [10, 0, 20],
            'taxon_B': [0, 5, 0],
            'taxon_C': [3, 4, 5]
        })
        
        result = process_batch(batch, ['taxon_A', 'taxon_B', 'taxon_C'])
        
        # Check that zeros are replaced
        assert (result['taxon_A'] > 0).all()
        assert (result['taxon_B'] > 0).all()
        assert (result['taxon_C'] > 0).all()
        
    def test_run_pipeline_with_temp_files(self):
        """Test full pipeline with temporary files."""
        # Create temporary input file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create test data
            test_data = pd.DataFrame({
                'participant_id': range(100),
                'taxon_A': np.random.poisson(10, 100),
                'taxon_B': np.random.poisson(5, 100),
                'taxon_C': np.random.poisson(15, 100)
            })
            # Introduce some zeros
            test_data.loc[0, 'taxon_A'] = 0
            test_data.loc[1, 'taxon_B'] = 0
            test_data.loc[2, 'taxon_C'] = 0
            
            test_data.to_parquet(input_path)
            
            # Run pipeline
            stats = run_zero_replacement_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                taxon_columns=['taxon_A', 'taxon_B', 'taxon_C']
            )
            
            # Verify output exists
            assert output_path.exists()
            assert stats['total_rows_processed'] == 100
            assert stats['taxon_columns_processed'] == 3
            
            # Verify output data has no zeros
            output_data = pd.read_parquet(output_path)
            assert (output_data['taxon_A'] > 0).all()
            assert (output_data['taxon_B'] > 0).all()
            assert (output_data['taxon_C'] > 0).all()
            
    def test_parameter_sensitivity(self):
        """Test that different alpha values produce different results."""
        counts = np.array([[0, 20], [15, 0]])
        concentrations = {'taxon_0': 1.0, 'taxon_1': 1.0}
        
        result_alpha_05 = bayesian_multiplicative_replace(counts, concentrations, alpha=0.5)
        result_alpha_10 = bayesian_multiplicative_replace(counts, concentrations, alpha=1.0)
        
        # Results should differ based on alpha
        assert not np.allclose(result_alpha_05, result_alpha_10)
        
    def test_empty_dataframe_handling(self):
        """Test handling of edge cases."""
        # Empty dataframe
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError):
            estimate_zero_replacement_params(empty_df, [])
            
    def test_all_zeros_handling(self):
        """Test handling of rows with all zeros."""
        counts = np.array([[0, 0, 0], [0, 0, 0]])
        concentrations = {'taxon_0': 1.0, 'taxon_1': 1.0, 'taxon_2': 1.0}
        
        result = bayesian_multiplicative_replace(counts, concentrations)
        
        # Should still produce positive values based on prior
        assert (result > 0).all()
        # Values should be roughly equal (prior-based)
        assert np.allclose(result[0], result[1])