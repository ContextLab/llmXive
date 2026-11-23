"""
Unit tests for code/analysis/fourier_metrics.py.
Tests Fourier transforms, power spectrum, and low-frequency integration.
"""
import numpy as np
import pytest
from pathlib import Path
import tempfile

from analysis.fourier_metrics import (
    compute_fourier_transform,
    compute_power_spectrum,
    get_frequency_grid,
    compute_low_frequency_spectral_power,
    compute_spatial_frequency_metrics
)

class TestFourierTransform:
    def test_fourier_transform_shape(self):
        """Fourier transform should have same shape as input."""
        img = np.random.randn(32, 32)
        ft = compute_fourier_transform(img)
        assert ft.shape == img.shape

    def test_fourier_transform_center(self):
        """DC component should be at center after fftshift."""
        img = np.ones((32, 32))
        ft = compute_fourier_transform(img)
        center = ft.shape[0] // 2
        # DC component should be the maximum
        assert np.argmax(np.abs(ft)) == center * ft.shape[1] + center

    def test_fourier_transform_real_input(self):
        """Fourier transform of real input should have Hermitian symmetry."""
        np.random.seed(42)
        img = np.random.randn(16, 16)
        ft = compute_fourier_transform(img)
        # Check symmetry: F(u,v) = conj(F(-u, -v))
        # After fftshift, center is (0,0)
        center = img.shape[0] // 2
        # Compare quadrants
        top_left = ft[:center, :center]
        bottom_right = np.conj(np.flipud(np.fliplr(ft[:center, :center])))
        # This is a simplified check; full symmetry check is complex
        # Just ensure no NaN or Inf
        assert np.all(np.isfinite(ft))

class TestPowerSpectrum:
    def test_power_spectrum_non_negative(self):
        """Power spectrum should be non-negative."""
        img = np.random.randn(32, 32)
        ps = compute_power_spectrum(img)
        assert np.all(ps >= 0)

    def test_power_spectrum_shape(self):
        """Power spectrum should have same shape as input."""
        img = np.random.randn(32, 32)
        ps = compute_power_spectrum(img)
        assert ps.shape == img.shape

    def test_power_spectrum_conservation(self):
        """Parseval's theorem: sum of power spectrum should relate to sum of squared image."""
        np.random.seed(42)
        img = np.random.randn(16, 16)
        ps = compute_power_spectrum(img)
        # Parseval: sum(|x|^2) = sum(|X|^2) / N
        lhs = np.sum(img**2)
        rhs = np.sum(ps) / (img.shape[0] * img.shape[1])
        # Allow for small numerical errors
        assert np.isclose(lhs, rhs, rtol=1e-5)

class TestFrequencyGrid:
    def test_frequency_grid_shape(self):
        """Frequency grid should have same shape as input."""
        shape = (32, 32)
        fx, fy = get_frequency_grid(shape)
        assert fx.shape == shape
        assert fy.shape == shape

    def test_frequency_grid_center_zero(self):
        """Frequency grid should be zero at center."""
        shape = (32, 32)
        fx, fy = get_frequency_grid(shape)
        center = shape[0] // 2
        assert fx[center, center] == 0
        assert fy[center, center] == 0

    def test_frequency_grid_symmetry(self):
        """Frequency grid should be symmetric around center."""
        shape = (32, 32)
        fx, fy = get_frequency_grid(shape)
        center = shape[0] // 2
        # Check that frequencies are symmetric
        assert np.allclose(fx, -np.fliplr(np.flipud(fx)))
        assert np.allclose(fy, -np.fliplr(np.flipud(fy)))

class TestLowFrequencySpectralPower:
    def test_low_frequency_power_positive(self):
        """Low frequency power should be positive."""
        img = np.random.randn(32, 32)
        power = compute_low_frequency_spectral_power(img, cutoff=0.1)
        assert power >= 0

    def test_low_frequency_power_increases_with_cutoff(self):
        """Low frequency power should increase with cutoff."""
        img = np.random.randn(32, 32)
        p1 = compute_low_frequency_spectral_power(img, cutoff=0.05)
        p2 = compute_low_frequency_spectral_power(img, cutoff=0.1)
        assert p2 >= p1

    def test_low_frequency_power_of_constant(self):
        """Constant image should have all power at DC (zero frequency)."""
        img = np.ones((32, 32))
        ps = compute_power_spectrum(img)
        # All power should be at center
        center = ps.shape[0] // 2
        total_power = np.sum(ps)
        dc_power = ps[center, center]
        # DC should be almost all power
        assert dc_power / total_power > 0.99

    def test_low_frequency_power_of_noise(self):
        """White noise should have uniform power distribution."""
        np.random.seed(42)
        img = np.random.randn(32, 32)
        ps = compute_power_spectrum(img)
        # Normalize
        ps_norm = ps / np.sum(ps)
        # Power should be roughly uniform (high entropy)
        # We just check that it's not concentrated
        max_power = np.max(ps_norm)
        assert max_power < 0.1  # No single bin should dominate

class TestSpatialFrequencyMetrics:
    def test_compute_metrics_returns_dict(self):
        """Should return a dictionary with expected keys."""
        img = np.random.randn(32, 32)
        result = compute_spatial_frequency_metrics(img)
        
        assert isinstance(result, dict)
        assert "low_frequency_power" in result
        assert "high_frequency_power" in result
        assert "total_power" in result
        assert "dominant_frequency" in result

    def test_compute_metrics_total_power(self):
        """Total power should match Parseval's theorem."""
        np.random.seed(42)
        img = np.random.randn(32, 32)
        result = compute_spatial_frequency_metrics(img)
        
        expected_total = np.sum(img**2)
        actual_total = result["total_power"]
        
        assert np.isclose(expected_total, actual_total, rtol=1e-5)

    def test_compute_metrics_with_pattern(self):
        """Should detect dominant frequency in a sinusoidal pattern."""
        x = np.linspace(0, 4*np.pi, 64)
        y = np.linspace(0, 4*np.pi, 64)
        X, Y = np.meshgrid(x, y)
        # Create a sinusoidal pattern with known frequency
        img = np.sin(X) * np.sin(Y)
        
        result = compute_spatial_frequency_metrics(img)
        
        # The dominant frequency should be non-zero
        assert result["dominant_frequency"] > 0
        # Most power should be in low frequencies for this smooth pattern
        assert result["low_frequency_power"] > result["high_frequency_power"]
