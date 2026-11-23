import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.correlations import apply_fdr_correction, compute_correlations

class TestFDRCorrection:
    """Test suite for FDR correction implementation (T016c)"""

    def setup_method(self):
        """Set up test fixtures"""
        # Create a temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.temp_dir)
        
        # Create sample correlation data
        self.sample_data = pd.DataFrame({
            'metric': ['pupil_peak', 'pupil_peak', 'pupil_mean', 'pupil_mean', 'pupil_q25'],
            'proxy': ['search_time', 'target_salience', 'search_time', 'fixation_count', 'target_salience'],
            'pearson_r': [0.65, -0.45, 0.72, 0.30, -0.20],
            'raw_p': [0.01, 0.05, 0.001, 0.15, 0.25],
            'method': ['pearson', 'pearson', 'pearson', 'pearson', 'pearson']
        })

    def teardown_method(self):
        """Clean up test artifacts"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fdr_correction_applied(self):
        """Test that FDR correction is applied correctly"""
        result = apply_fdr_correction(self.sample_data.copy())
        
        # Check that 'adj_p' column exists
        assert 'adj_p' in result.columns, "FDR correction should add 'adj_p' column"
        
        # Check that all adjusted p-values are <= 1.0
        assert all(result['adj_p'] <= 1.0), "All adjusted p-values should be <= 1.0"
        
        # Check that adjusted p-values are non-negative
        assert all(result['adj_p'] >= 0), "All adjusted p-values should be non-negative"

    def test_fdr_monotonicity(self):
        """Test that adjusted p-values are monotonically increasing when sorted by raw p"""
        result = apply_fdr_correction(self.sample_data.copy())
        
        # Sort by raw p-value
        sorted_result = result.sort_values('raw_p')
        
        # Check monotonicity
        for i in range(1, len(sorted_result)):
            assert sorted_result.iloc[i]['adj_p'] >= sorted_result.iloc[i-1]['adj_p'], \
                "Adjusted p-values should be monotonically increasing"

    def test_fdr_replaces_raw_p(self):
        """Test that adj_p replaces raw_p as the primary reported p-value"""
        result = apply_fdr_correction(self.sample_data.copy())
        
        # The constraint states: "adj_p MUST replace raw_p as the primary reported p-value"
        # This means the 'raw_p' column should now contain the adjusted values
        assert 'raw_p' in result.columns, "raw_p column should still exist"
        
        # Check that raw_p now contains the adjusted values
        pd.testing.assert_series_equal(result['raw_p'], result['adj_p'], 
                                     check_names=False, check_dtype=False)

    def test_fdr_with_small_p_values(self):
        """Test FDR correction with very small p-values"""
        small_p_data = pd.DataFrame({
            'metric': ['m1', 'm2', 'm3'],
            'proxy': ['p1', 'p2', 'p3'],
            'pearson_r': [0.8, 0.7, 0.6],
            'raw_p': [0.0001, 0.001, 0.01],
            'method': ['pearson', 'pearson', 'pearson']
        })
        
        result = apply_fdr_correction(small_p_data.copy())
        
        # The smallest p-value should remain small but be adjusted
        assert result['adj_p'].iloc[0] > 0.0001, "Smallest p-value should be adjusted upward"
        assert result['adj_p'].iloc[0] < 0.001, "Smallest adjusted p-value should still be small"

    def test_fdr_with_large_p_values(self):
        """Test FDR correction with large p-values"""
        large_p_data = pd.DataFrame({
            'metric': ['m1', 'm2'],
            'proxy': ['p1', 'p2'],
            'pearson_r': [0.1, 0.2],
            'raw_p': [0.8, 0.9],
            'method': ['pearson', 'pearson']
        })
        
        result = apply_fdr_correction(large_p_data.copy())
        
        # Large p-values should be adjusted upward but capped at 1.0
        assert all(result['adj_p'] <= 1.0), "Adjusted p-values should be capped at 1.0"
        
        # The largest p-value should remain close to 1.0
        assert result['adj_p'].iloc[-1] >= 0.9, "Largest p-value should remain large"

    def test_fdr_with_single_value(self):
        """Test FDR correction with a single p-value"""
        single_data = pd.DataFrame({
            'metric': ['m1'],
            'proxy': ['p1'],
            'pearson_r': [0.5],
            'raw_p': [0.05],
            'method': ['pearson']
        })
        
        result = apply_fdr_correction(single_data.copy())
        
        # For a single value, the adjusted p-value should equal the raw p-value
        assert abs(result['adj_p'].iloc[0] - 0.05) < 1e-10, \
            "Single p-value should remain unchanged"

    def test_fdr_preserves_other_columns(self):
        """Test that FDR correction preserves other columns"""
        result = apply_fdr_correction(self.sample_data.copy())
        
        # Check that all original columns (except raw_p) are preserved
        expected_cols = {'metric', 'proxy', 'pearson_r', 'method', 'adj_p', 'raw_p'}
        assert set(result.columns) == expected_cols, \
            f"Expected columns {expected_cols}, got {set(result.columns)}"

    def test_fdr_with_nan_values(self):
        """Test FDR correction with NaN values in raw_p"""
        nan_data = pd.DataFrame({
            'metric': ['m1', 'm2', 'm3'],
            'proxy': ['p1', 'p2', 'p3'],
            'pearson_r': [0.5, 0.6, 0.7],
            'raw_p': [0.05, np.nan, 0.15],
            'method': ['pearson', 'pearson', 'pearson']
        })
        
        # This should handle NaN values gracefully
        result = apply_fdr_correction(nan_data.copy())
        
        # Check that NaN handling doesn't crash
        assert result is not None, "Function should handle NaN values without crashing"
        
        # The NaN value should be preserved or handled appropriately
        # (implementation-dependent, but should not cause an error)

    def test_integration_with_pipeline(self):
        """Test that FDR correction integrates with the full pipeline"""
        # This test verifies that the FDR correction can be applied to the output
        # of the compute_correlations function
        
        # Create a minimal DataFrame that mimics the output of compute_correlations
        test_data = pd.DataFrame({
            'metric': ['pupil_peak'],
            'proxy': ['search_time'],
            'pearson_r': [0.5],
            'raw_p': [0.05],
            'method': ['pearson']
        })
        
        # Apply FDR correction
        result = apply_fdr_correction(test_data)
        
        # Verify the result
        assert 'adj_p' in result.columns
        assert len(result) == 1
        assert result['adj_p'].iloc[0] >= 0.05  # Adjusted p-value should be >= raw p-value
