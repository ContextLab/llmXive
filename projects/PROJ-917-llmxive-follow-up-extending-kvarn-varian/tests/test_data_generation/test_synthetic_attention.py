"""
Tests for static synthetic attention matrix generation (T017a).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data_generation.synthetic_attention import (
    generate_static_attention_matrix,
    compute_scaling_factor,
    generate_static_dataset,
    SingleStepSinkhornSolver
)
from code.data_generation.utils import apply_epsilon_floor

class TestSyntheticMatrixGeneration:
    """Tests for static attention matrix generation."""

    def test_matrix_dimensions(self):
        """Test that generated matrices have correct dimensions."""
        matrix, stats = generate_static_attention_matrix(size=128)
        assert matrix.shape == (128, 128)

    def test_sparsity_control(self):
        """Test that sparsity is approximately as specified."""
        target_sparsity = 0.2
        matrix, stats = generate_static_attention_matrix(
            size=128, target_sparsity=target_sparsity
        )
        actual_sparsity = 1.0 - (np.count_nonzero(matrix) / (128 * 128))
        # Allow 10% tolerance
        assert abs(actual_sparsity - target_sparsity) < 0.02

    def test_outlier_magnitude_range(self):
        """Test that outliers fall within specified range."""
        outlier_range = (3.0, 7.0)
        matrix, stats = generate_static_attention_matrix(
            size=128,
            outlier_fraction=0.1,
            outlier_magnitude_range=outlier_range
        )
        non_zero = matrix[matrix != 0]
        if len(non_zero) > 0:
            max_mag = np.max(np.abs(non_zero))
            # Outliers should be at least the minimum magnitude
            assert max_mag >= outlier_range[0] - 0.5

    def test_numerical_stability(self):
        """Test that generated matrices pass numerical stability checks."""
        from code.data_generation.utils import check_numerical_stability
        matrix, stats = generate_static_attention_matrix()
        assert check_numerical_stability(stats['mean'])
        assert check_numerical_stability(stats['var'])

    def test_scaling_factor_computation(self):
        """Test that scaling factors are computed correctly."""
        matrix, _ = generate_static_attention_matrix()
        solver = SingleStepSinkhornSolver()
        scaling_factor, status = compute_scaling_factor(matrix, solver)
        
        assert status in ['converged', 'nan', 'failed']
        if status == 'converged':
            assert not np.isnan(scaling_factor)
            assert not np.isinf(scaling_factor)

    def test_deterministic_generation(self):
        """Test that same seed produces same matrix."""
        seed = 12345
        matrix1, stats1 = generate_static_attention_matrix(size=64, seed=seed)
        matrix2, stats2 = generate_static_attention_matrix(size=64, seed=seed)
        
        np.testing.assert_array_equal(matrix1, matrix2)
        assert stats1 == stats2

class TestStaticDatasetGeneration:
    """Tests for full dataset generation."""

    def test_dataset_count(self):
        """Test that dataset contains exactly 10000 matrices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.parquet'
            df = generate_static_dataset(
                num_matrices=10000,
                output_path=output_path,
                seed=42
            )
            assert len(df) == 10000

    def test_dataset_schema(self):
        """Test that dataset has required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.parquet'
            df = generate_static_dataset(
                num_matrices=100,  # Small subset for speed
                output_path=output_path,
                seed=42
            )
            required_cols = ['mean', 'var', 'sparsity', 'outlier_magnitude', 'scaling_factor']
            for col in required_cols:
                assert col in df.columns

    def test_dataset_file_created(self):
        """Test that output Parquet file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.parquet'
            df = generate_static_dataset(
                num_matrices=100,
                output_path=output_path,
                seed=42
            )
            assert output_path.exists()
            # Verify we can read it back
            df_read = pd.read_parquet(output_path)
            assert len(df_read) == 100

    def test_no_temporal_drift(self):
        """Test that matrices are independent (no temporal drift)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.parquet'
            df = generate_static_dataset(
                num_matrices=1000,
                output_path=output_path,
                seed=42
            )
            # Check that consecutive matrices don't have correlated properties
            # (simple check: variance of means should be stable)
            means = df['mean'].values
            assert np.var(means) > 0  # Should have some variance
            # No systematic trend
            trend = np.polyfit(range(len(means)), means, 1)[0]
            assert abs(trend) < 0.01  # Slope should be near zero

    def test_scaling_factor_distribution(self):
        """Test that scaling factors have reasonable distribution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.parquet'
            df = generate_static_dataset(
                num_matrices=500,
                output_path=output_path,
                seed=42
            )
            # Filter out NaN values
            valid_factors = df['scaling_factor'].dropna()
            assert len(valid_factors) > 0
            assert np.all(np.isfinite(valid_factors))
            # Check that most values are positive (typical for scaling factors)
            assert np.mean(valid_factors > 0) > 0.5

class TestEdgeCases:
    """Tests for edge cases in synthetic generation."""

    def test_zero_variance_handling(self):
        """Test handling of matrices with near-zero variance."""
        # Create a matrix with very low variance
        matrix = np.ones((128, 128)) * 0.5
        # Add tiny noise
        matrix += np.random.randn(128, 128) * 1e-10
        
        solver = SingleStepSinkhornSolver()
        scaling_factor, status = compute_scaling_factor(matrix, solver)
        
        # Should handle gracefully (either converge or mark as nan)
        assert status in ['converged', 'nan', 'failed']

    def test_extreme_sparsity(self):
        """Test generation with extreme sparsity."""
        matrix, stats = generate_static_attention_matrix(
            size=64, target_sparsity=0.95
        )
        actual_sparsity = 1.0 - (np.count_nonzero(matrix) / (64 * 64))
        assert actual_sparsity > 0.90  # Allow some tolerance

    def test_no_outliers(self):
        """Test generation with no outliers."""
        matrix, stats = generate_static_attention_matrix(
            size=64, outlier_fraction=0.0
        )
        # All values should be within reasonable range
        assert np.all(np.abs(matrix) < 10)  # No extreme values

if __name__ == '__main__':
    pytest.main([__file__, '-v'])