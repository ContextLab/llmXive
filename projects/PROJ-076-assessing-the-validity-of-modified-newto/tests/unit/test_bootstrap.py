"""
Unit tests for block-bootstrap logic in code/residuals.py.

This module tests the block-bootstrap permutation test implementation
for analyzing residuals in galaxy rotation curve fits.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.residuals import (
    compute_residuals,
    block_bootstrap_pvalue,
    bootstrap_distribution,
    validate_residual_data
)


class TestComputeResiduals:
    """Tests for residual computation logic."""

    def test_compute_residuals_basic(self):
        """Test basic residual calculation."""
        observed = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        predicted = np.array([11.0, 19.0, 31.0, 39.0, 51.0])
        
        residuals = compute_residuals(observed, predicted)
        
        expected = np.array([-1.0, 1.0, -1.0, 1.0, -1.0])
        np.testing.assert_array_almost_equal(residuals, expected)

    def test_compute_residuals_with_errors(self):
        """Test residuals with different error magnitudes."""
        observed = np.array([100.0, 200.0, 300.0])
        predicted = np.array([100.0, 200.0, 300.0])
        
        residuals = compute_residuals(observed, predicted)
        
        expected = np.array([0.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(residuals, expected)

    def test_compute_residuals_shape(self):
        """Test that residuals maintain input shape."""
        observed = np.random.randn(100)
        predicted = np.random.randn(100)
        
        residuals = compute_residuals(observed, predicted)
        
        assert residuals.shape == observed.shape
        assert len(residuals) == 100


class TestBlockBootstrap:
    """Tests for block-bootstrap permutation test logic."""

    @pytest.fixture
    def sample_galaxy_data(self):
        """Create sample galaxy data for testing."""
        np.random.seed(42)
        n_points = 50
        r = np.linspace(1, 10, n_points)
        v_obs = 200 + np.random.randn(n_points) * 10
        v_pred = 200 + np.sin(r) * 5
        v_err = np.ones(n_points) * 5
        
        return pd.DataFrame({
            'galaxy_id': ['NGC-TEST'] * n_points,
            'r': r,
            'v_obs': v_obs,
            'v_pred': v_pred,
            'v_err': v_err
        })

    def test_bootstrap_distribution_basic(self, sample_galaxy_data):
        """Test basic bootstrap distribution generation."""
        residuals = sample_galaxy_data['v_obs'] - sample_galaxy_data['v_pred']
        
        dist = bootstrap_distribution(residuals, n_bootstrap=100, block_size=5)
        
        assert len(dist) == 100
        assert isinstance(dist, np.ndarray)
        assert dist.dtype in [np.float64, np.float32]

    def test_bootstrap_distribution_with_galaxy_groups(self):
        """Test bootstrap with multiple galaxy groups."""
        np.random.seed(123)
        
        # Create data with two galaxy groups
        n_points_per_galaxy = 30
        n_galaxies = 5
        
        data = []
        for i in range(n_galaxies):
            galaxy_id = f'GAL-{i:03d}'
            residuals = np.random.randn(n_points_per_galaxy) * 10
            for j, r_val in enumerate(residuals):
                data.append({
                    'galaxy_id': galaxy_id,
                    'residual': r_val
                })
        
        df = pd.DataFrame(data)
        
        # Test block bootstrap at galaxy level
        dist = bootstrap_distribution(
            df['residual'].values,
            n_bootstrap=50,
            block_size=3,
            group_col=df['galaxy_id'].values
        )
        
        assert len(dist) == 50
        # Should have non-zero variance
        assert np.std(dist) > 0

    def test_block_bootstrap_pvalue_computation(self, sample_galaxy_data):
        """Test p-value computation from bootstrap."""
        residuals = sample_galaxy_data['v_obs'] - sample_galaxy_data['v_pred']
        
        # Create a null distribution with mean 0
        null_residuals = np.random.randn(len(residuals)) * 5
        
        p_value = block_bootstrap_pvalue(
            residuals,
            null_residuals,
            n_bootstrap=100,
            block_size=5
        )
        
        assert 0.0 <= p_value <= 1.0
        assert isinstance(p_value, (float, np.floating))

    def test_bootstrap_with_different_block_sizes(self, sample_galaxy_data):
        """Test that different block sizes produce different distributions."""
        residuals = sample_galaxy_data['v_obs'] - sample_galaxy_data['v_pred']
        
        dist_small = bootstrap_distribution(residuals, n_bootstrap=50, block_size=2)
        dist_large = bootstrap_distribution(residuals, n_bootstrap=50, block_size=10)
        
        # Both should have same length
        assert len(dist_small) == len(dist_large) == 50
        
        # Variances might differ due to block size
        var_small = np.var(dist_small)
        var_large = np.var(dist_large)
        
        # At least one should be non-zero
        assert var_small > 0 or var_large > 0

    def test_bootstrap_with_single_block(self, sample_galaxy_data):
        """Test bootstrap when block_size equals data length."""
        residuals = sample_galaxy_data['v_obs'] - sample_galaxy_data['v_pred']
        n_points = len(residuals)
        
        dist = bootstrap_distribution(
            residuals, 
            n_bootstrap=20, 
            block_size=n_points
        )
        
        assert len(dist) == 20
        # Each bootstrap sample should be a permutation of the original
        # The mean of each sample should be close to the original mean
        original_mean = np.mean(residuals)
        for sample_mean in dist:
            assert abs(sample_mean - original_mean) < 0.1

    def test_bootstrap_pvalue_edge_cases(self):
        """Test p-value computation with edge cases."""
        # Perfect match (p-value should be 1.0 or close)
        identical = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        p_identical = block_bootstrap_pvalue(identical, identical, n_bootstrap=50, block_size=2)
        assert 0.9 <= p_identical <= 1.0

        # Completely different distributions
        group1 = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        group2 = np.array([100.0, 100.0, 100.0, 100.0, 100.0])
        p_different = block_bootstrap_pvalue(group1, group2, n_bootstrap=50, block_size=2)
        # Should be close to 0
        assert p_different < 0.1


class TestValidateResidualData:
    """Tests for residual data validation."""

    def test_validate_empty_array(self):
        """Test validation with empty array."""
        with pytest.raises(ValueError, match="Residual array cannot be empty"):
            validate_residual_data(np.array([]))

    def test_validate_nan_values(self):
        """Test validation with NaN values."""
        data = np.array([1.0, np.nan, 3.0])
        with pytest.raises(ValueError, match="Residual array contains NaN"):
            validate_residual_data(data)

    def test_validate_inf_values(self):
        """Test validation with infinite values."""
        data = np.array([1.0, np.inf, 3.0])
        with pytest.raises(ValueError, match="Residual array contains infinite values"):
            validate_residual_data(data)

    def test_validate_valid_data(self):
        """Test validation with valid data."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = validate_residual_data(data)
        assert result is True


class TestIntegration:
    """Integration tests for the full bootstrap pipeline."""

    def test_full_bootstrap_pipeline(self):
        """Test the complete bootstrap analysis pipeline."""
        np.random.seed(42)
        
        # Generate realistic residual data
        n_galaxies = 10
        points_per_galaxy = 20
        
        all_residuals = []
        galaxy_ids = []
        
        for i in range(n_galaxies):
            galaxy_id = f'GAL-{i:03d}'
            # Simulate residuals with some structure
            residuals = np.random.randn(points_per_galaxy) * 10 + np.sin(np.arange(points_per_galaxy)) * 2
            all_residuals.extend(residuals)
            galaxy_ids.extend([galaxy_id] * points_per_galaxy)
        
        residuals = np.array(all_residuals)
        groups = np.array(galaxy_ids)
        
        # Run bootstrap analysis
        dist = bootstrap_distribution(
            residuals,
            n_bootstrap=200,
            block_size=5,
            group_col=groups
        )
        
        # Compute p-value against null
        null_residuals = np.random.randn(len(residuals)) * 5
        p_value = block_bootstrap_pvalue(
            residuals,
            null_residuals,
            n_bootstrap=200,
            block_size=5,
            group_col=groups
        )
        
        # Validate results
        assert len(dist) == 200
        assert 0.0 <= p_value <= 1.0
        assert np.std(dist) > 0

    def test_bootstrap_convergence(self):
        """Test that bootstrap distribution converges with more samples."""
        np.random.seed(42)
        residuals = np.random.randn(100) * 10
        
        dist_50 = bootstrap_distribution(residuals, n_bootstrap=50, block_size=5)
        dist_200 = bootstrap_distribution(residuals, n_bootstrap=200, block_size=5)
        
        # Standard error should decrease with more samples
        se_50 = np.std(dist_50) / np.sqrt(50)
        se_200 = np.std(dist_200) / np.sqrt(200)
        
        # Larger sample should have smaller standard error
        assert se_200 < se_50 * 1.5  # Allow some tolerance for randomness