"""
Unit tests for Phase Locking Value (PLV) calculation.
"""
import numpy as np
import pytest
from src.analysis.plv import compute_plv, compute_plv_batch, plv_calc

class TestComputePLV:
    def test_perfectly_synchronized_signals(self):
        """Test PLV with identical signals (should be 1.0)."""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 10 * t)
        
        plv = compute_plv(signal, signal)
        assert np.isclose(plv, 1.0, atol=1e-5)

    def test_perfectly_anti_synchronized_signals(self):
        """Test PLV with phase-shifted pi signals (should be 1.0)."""
        t = np.linspace(0, 1, 1000)
        signal1 = np.sin(2 * np.pi * 10 * t)
        signal2 = np.sin(2 * np.pi * 10 * t + np.pi)
        
        plv = compute_plv(signal1, signal2)
        # PLV measures phase consistency, not sign. pi shift is consistent.
        assert np.isclose(plv, 1.0, atol=1e-5)

    def test_random_phase_signals(self):
        """Test PLV with uncorrelated random noise (should be close to 0)."""
        np.random.seed(42)
        signal1 = np.random.randn(1000)
        signal2 = np.random.randn(1000)
        
        plv = compute_plv(signal1, signal2)
        # With random noise, PLV should be low, but not exactly 0 due to finite samples
        assert plv < 0.3

    def test_shape_mismatch_raises_error(self):
        """Test that mismatched shapes raise ValueError."""
        signal1 = np.random.randn(100)
        signal2 = np.random.randn(200)
        
        with pytest.raises(ValueError):
            compute_plv(signal1, signal2)

    def test_ndim_mismatch_raises_error(self):
        """Test that 2D input to compute_plv raises ValueError."""
        signal1 = np.random.randn(100, 10)
        signal2 = np.random.randn(100, 10)
        
        with pytest.raises(ValueError):
            compute_plv(signal1, signal2)

class TestComputePLVBatch:
    def test_batch_perfect_sync(self):
        """Test batch PLV with perfectly synchronized signals."""
        n_signals = 5
        t = np.linspace(0, 1, 1000)
        base_signal = np.sin(2 * np.pi * 10 * t)
        
        signals1 = np.tile(base_signal, (n_signals, 1))
        signals2 = np.tile(base_signal, (n_signals, 1))
        
        plv_values = compute_plv_batch(signals1, signals2)
        assert np.allclose(plv_values, 1.0, atol=1e-5)

    def test_batch_shape_mismatch(self):
        """Test that batch shape mismatch raises ValueError."""
        signals1 = np.random.randn(5, 100)
        signals2 = np.random.randn(5, 200)
        
        with pytest.raises(ValueError):
            compute_plv_batch(signals1, signals2)

    def test_batch_ndim_mismatch(self):
        """Test that 1D input to compute_plv_batch raises ValueError."""
        signal1 = np.random.randn(100)
        signal2 = np.random.randn(100)
        
        with pytest.raises(ValueError):
            compute_plv_batch(signal1, signal2)

class TestPLVCalc:
    def test_plv_calc_wrapper(self):
        """Test that plv_calc wrapper works correctly."""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 10 * t)
        
        result = plv_calc(signal, signal)
        assert isinstance(result, float)
        assert np.isclose(result, 1.0, atol=1e-5)

    def test_plv_calc_vs_compute_plv(self):
        """Test that plv_calc produces same results as compute_plv."""
        np.random.seed(123)
        signal1 = np.random.randn(1000)
        signal2 = np.random.randn(1000)
        
        result_wrapper = plv_calc(signal1, signal2)
        result_direct = compute_plv(signal1, signal2)
        
        assert np.isclose(result_wrapper, result_direct)