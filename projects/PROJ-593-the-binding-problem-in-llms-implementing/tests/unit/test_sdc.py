import numpy as np
import pytest
from src.analysis.sdc import spectral_density_correlation, compute_sdc_batch

class TestSpectralDensityCorrelation:
    """Unit tests for Spectral Density Correlation (SDC) calculation."""

    def test_perfect_correlation(self):
        """Test that identical signals yield correlation of 1.0."""
        psd = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = spectral_density_correlation(psd, psd)
        assert np.isclose(result, 1.0, atol=1e-5)

    def test_perfect_negative_correlation(self):
        """Test that perfectly inverse signals yield correlation of -1.0."""
        psd_model = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        psd_meg = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
        result = spectral_density_correlation(psd_model, psd_meg)
        assert np.isclose(result, -1.0, atol=1e-5)

    def test_no_correlation(self):
        """Test that uncorrelated signals yield correlation near 0."""
        # Create two signals with no linear relationship
        np.random.seed(42)
        psd_model = np.random.randn(100)
        psd_meg = np.random.randn(100)
        result = spectral_density_correlation(psd_model, psd_meg)
        # With random data, correlation should be small, but not necessarily exactly 0
        assert abs(result) < 0.3  # Loose threshold for random data

    def test_different_lengths_raises_error(self):
        """Test that mismatched lengths raise ValueError."""
        psd_model = np.array([1.0, 2.0, 3.0])
        psd_meg = np.array([1.0, 2.0])
        with pytest.raises(ValueError, match="same length"):
            spectral_density_correlation(psd_model, psd_meg)

    def test_non_1d_raises_error(self):
        """Test that non-1D inputs raise ValueError."""
        psd_model = np.array([[1.0, 2.0], [3.0, 4.0]])
        psd_meg = np.array([1.0, 2.0, 3.0, 4.0])
        with pytest.raises(ValueError, match="1-dimensional"):
            spectral_density_correlation(psd_model, psd_meg)

    def test_normalization_to_unit_area(self):
        """Test that normalization to unit area is applied correctly."""
        # Create two signals that are identical in shape but different in magnitude
        psd_model = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
        psd_meg = np.array([2.0, 4.0, 6.0, 4.0, 2.0])  # Exactly 2x psd_model
        
        # Without normalization, they are perfectly correlated
        # With normalization, they should still be perfectly correlated
        result = spectral_density_correlation(psd_model, psd_meg, normalize=True)
        assert np.isclose(result, 1.0, atol=1e-5)

    def test_constant_signal(self):
        """Test behavior with constant (zero variance) signal."""
        psd_model = np.ones(10)
        psd_meg = np.ones(10)
        # When variance is zero, correlation is undefined (NaN), 
        # but our implementation should return 0.0
        result = spectral_density_correlation(psd_model, psd_meg)
        assert result == 0.0

class TestComputeSDCBatch:
    """Unit tests for batch SDC computation."""

    def test_batch_calculation(self):
        """Test batch calculation against single calculation."""
        np.random.seed(123)
        batch_size = 5
        freq_bins = 50
        
        psd_models = np.random.randn(batch_size, freq_bins)
        psd_meg = np.random.randn(freq_bins)
        
        batch_result = compute_sdc_batch(psd_models, psd_meg)
        
        assert batch_result.shape == (batch_size,)
        
        # Verify each batch element matches individual calculation
        for i in range(batch_size):
            expected = spectral_density_correlation(psd_models[i], psd_meg)
            assert np.isclose(batch_result[i], expected)

    def test_invalid_dimensions(self):
        """Test that invalid input dimensions raise errors."""
        psd_models_1d = np.random.randn(10)
        psd_meg = np.random.randn(10)
        
        with pytest.raises(ValueError, match="2D"):
            compute_sdc_batch(psd_models_1d, psd_meg)
        
        psd_models_2d = np.random.randn(5, 10)
        psd_meg_2d = np.random.randn(1, 10)
        
        with pytest.raises(ValueError, match="1D"):
            compute_sdc_batch(psd_models_2d, psd_meg_2d)
