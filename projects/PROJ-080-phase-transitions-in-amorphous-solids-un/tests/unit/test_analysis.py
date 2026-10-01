import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import the functions to test
from code.analysis import aggregate_to_shear_bands, perform_ks_test, apply_bonferroni_correction

class TestAggregateToShearBands:
    def test_aggregate_creates_correct_columns(self):
        """Test that aggregation creates the required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            
            # Create dummy data with x, y, d2_min
            df = pd.DataFrame({
                'x': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
                'y': [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
                'd2_min': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
            })
            df.to_csv(input_path, index=False)
            
            aggregate_to_shear_bands(str(input_path), str(output_path), k=3, seed=42)
            
            assert output_path.exists()
            result = pd.read_csv(output_path)
            
            assert 'shear_band_id' in result.columns
            assert 'mean_D2_min' in result.columns
            assert 'particle_count' in result.columns
            
            # Check types
            assert result['shear_band_id'].dtype in ['int64', 'int32']
            assert result['particle_count'].dtype in ['int64', 'int32']

    def test_aggregate_deterministic_with_seed(self):
        """Test that clustering is deterministic with fixed seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path1 = Path(tmpdir) / 'output1.csv'
            output_path2 = Path(tmpdir) / 'output2.csv'
            
            df = pd.DataFrame({
                'x': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
                'y': [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
                'd2_min': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
            })
            df.to_csv(input_path, index=False)
            
            aggregate_to_shear_bands(str(input_path), str(output_path1), k=3, seed=42)
            aggregate_to_shear_bands(str(input_path), str(output_path2), k=3, seed=42)
            
            res1 = pd.read_csv(output_path1)
            res2 = pd.read_csv(output_path2)
            
            # Results should be identical
            pd.testing.assert_frame_equal(res1, res2)

    def test_fallback_to_index_clustering(self):
        """Test fallback when no spatial columns exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            
            # Data without x, y, z
            df = pd.DataFrame({
                'd2_min': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
            })
            df.to_csv(input_path, index=False)
            
            # Should not raise, should use index clustering
            aggregate_to_shear_bands(str(input_path), str(output_path), k=3, seed=42)
            
            assert output_path.exists()
            result = pd.read_csv(output_path)
            assert len(result) == 3  # k=3 bands

class TestPerformKsTest:
    def test_ks_test_returns_valid_stats(self):
        """Test KS test returns valid statistic and p-value."""
        brittle_df = pd.DataFrame({'mean_D2_min': [0.1, 0.2, 0.3]})
        ductile_df = pd.DataFrame({'mean_D2_min': [0.4, 0.5, 0.6]})
        
        stat, pval = perform_ks_test(brittle_df, ductile_df)
        
        assert 0 <= stat <= 1.0
        assert 0 <= pval <= 1.0

    def test_ks_test_detects_difference(self):
        """Test KS test detects significant difference."""
        # Two distinct distributions
        brittle_df = pd.DataFrame({'mean_D2_min': [0.1] * 50})
        ductile_df = pd.DataFrame({'mean_D2_min': [0.9] * 50})
        
        stat, pval = perform_ks_test(brittle_df, ductile_df)
        
        # Should be very significant
        assert pval < 0.05

    def test_ks_test_empty_data_raises(self):
        """Test KS test raises on empty data."""
        with pytest.raises(ValueError):
            perform_ks_test(pd.DataFrame(), pd.DataFrame({'mean_D2_min': [0.1]}))

class TestBonferroniCorrection:
    def test_correction_scales_p_values(self):
        """Test that p-values are scaled by num_tests."""
        p_values = [0.01, 0.05, 0.1]
        num_tests = 5
        
        corrected = apply_bonferroni_correction(p_values, num_tests)
        
        expected = [0.05, 0.25, 0.5]
        np.testing.assert_array_almost_equal(corrected, expected)

    def test_correction_caps_at_one(self):
        """Test that corrected p-values do not exceed 1.0."""
        p_values = [0.5, 0.9]
        num_tests = 10
        
        corrected = apply_bonferroni_correction(p_values, num_tests)
        
        assert all(p <= 1.0 for p in corrected)
        assert corrected[0] == 1.0  # 0.5 * 10 = 5.0 -> capped to 1.0
        assert corrected[1] == 1.0

    def test_zero_tests_returns_original(self):
        """Test that zero tests returns original p-values."""
        p_values = [0.01, 0.05]
        corrected = apply_bonferroni_correction(p_values, 0)
        assert corrected == p_values
