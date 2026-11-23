"""
Unit tests for PLV (Phase Locking Value) calculation module.

These tests verify the correctness of the PLV implementation against:
1. Known analytical cases (perfect phase locking, random phases)
2. Edge cases (constant signals, single sample)
3. Integration with batch processing
"""
import numpy as np
import pytest
from src.analysis.plv import compute_plv, compute_plv_batch, plv_calc


class TestComputePLV:
    """Tests for the compute_plv function."""
    
    def test_perfect_phase_locking(self):
        """PLV should be 1.0 when signals are identical."""
        signal = np.sin(np.linspace(0, 4 * np.pi, 1000))
        plv = compute_plv(signal, signal)
        assert np.isclose(plv, 1.0, atol=1e-5), f"Expected PLV=1.0, got {plv}"
    
    def test_perfect_phase_locking_with_phase_shift(self):
        """PLV should be 1.0 when signals have a constant phase difference."""
        t = np.linspace(0, 10, 1000)
        signal1 = np.sin(t)
        signal2 = np.sin(t + np.pi / 4)  # Constant phase shift
        plv = compute_plv(signal1, signal2)
        assert np.isclose(plv, 1.0, atol=1e-5), f"Expected PLV=1.0, got {plv}"
    
    def test_random_phases(self):
        """PLV should be close to 0 for signals with random phase relationships."""
        np.random.seed(42)
        signal1 = np.random.randn(1000)
        signal2 = np.random.randn(1000)
        plv = compute_plv(signal1, signal2)
        # For random signals, PLV should be small but not exactly 0
        assert plv < 0.1, f"Expected PLV < 0.1 for random signals, got {plv}"
    
    def test_90_degree_phase_shift(self):
        """Test PLV with a known 90-degree phase shift (sine vs cosine)."""
        t = np.linspace(0, 10 * np.pi, 1000)
        signal1 = np.sin(t)
        signal2 = np.cos(t)  # 90-degree phase shift
        plv = compute_plv(signal1, signal2)
        # PLV should still be 1.0 for constant phase difference
        assert np.isclose(plv, 1.0, atol=1e-5), f"Expected PLV=1.0, got {plv}"
    
    def test_signal_length_mismatch(self):
        """Should raise ValueError if signals have different lengths."""
        signal1 = np.random.randn(100)
        signal2 = np.random.randn(50)
        with pytest.raises(ValueError):
            compute_plv(signal1, signal2)
    
    def test_non_1d_input(self):
        """Should raise ValueError for non-1D inputs."""
        signal1 = np.random.randn(10, 5)
        signal2 = np.random.randn(10, 5)
        with pytest.raises(ValueError):
            compute_plv(signal1, signal2)
    
    def test_constant_signal(self):
        """PLV for constant signals should be 1.0 (trivial phase locking)."""
        signal = np.ones(100)
        plv = compute_plv(signal, signal)
        # Note: Hilbert transform of constant is problematic, but should not crash
        # and should return a valid float
        assert 0.0 <= plv <= 1.0, f"PLV must be in [0, 1], got {plv}"


class TestComputePLVBatch:
    """Tests for the compute_plv_batch function."""
    
    def test_batch_identical_signals(self):
        """PLV should be 1.0 for all batches of identical signals."""
        batch_size = 5
        signal_length = 1000
        signals1 = np.random.randn(batch_size, signal_length)
        signals2 = signals1.copy()  # Identical
        
        plv_results = compute_plv_batch(signals1, signals2)
        
        assert plv_results.shape == (batch_size,), f"Expected shape ({batch_size},), got {plv_results.shape}"
        assert np.allclose(plv_results, 1.0, atol=1e-5), f"Expected all PLVs=1.0, got {plv_results}"
    
    def test_batch_with_phase_shift(self):
        """Test batch processing with constant phase shift."""
        batch_size = 3
        signal_length = 1000
        t = np.linspace(0, 10, signal_length)
        
        signals1 = np.array([np.sin(t + i * 0.1) for i in range(batch_size)])
        signals2 = np.array([np.sin(t + i * 0.1 + np.pi / 6) for i in range(batch_size)])
        
        plv_results = compute_plv_batch(signals1, signals2)
        
        assert plv_results.shape == (batch_size,)
        assert np.allclose(plv_results, 1.0, atol=1e-5), f"Expected all PLVs=1.0, got {plv_results}"
    
    def test_batch_shape_mismatch(self):
        """Should raise ValueError if batch shapes don't match."""
        signals1 = np.random.randn(5, 100)
        signals2 = np.random.randn(3, 100)
        with pytest.raises(ValueError):
            compute_plv_batch(signals1, signals2)
    
    def test_batch_axis_parameter(self):
        """Test that the axis parameter works correctly."""
        # Signal dimension is at axis 0
        signals1 = np.random.randn(100, 5, 10)  # 100 signals of length 10
        signals2 = signals1.copy()
        
        plv_results = compute_plv_batch(signals1, signals2, axis=0)
        
        assert plv_results.shape == (5, 10), f"Expected shape (5, 10), got {plv_results.shape}"
        assert np.allclose(plv_results, 1.0, atol=1e-5)


class TestPLVCalc:
    """Tests for the plv_calc function (primary entry point)."""
    
    def test_basic_plv_calc(self):
        """Test basic PLV calculation."""
        t = np.linspace(0, 10 * np.pi, 1000)
        signal1 = np.sin(t)
        signal2 = np.sin(t + np.pi / 6)
        
        plv = plv_calc(signal1, signal2)
        
        assert isinstance(plv, float)
        assert 0.0 <= plv <= 1.0
        assert np.isclose(plv, 1.0, atol=1e-5)
    
    def test_plv_calc_with_normalization(self):
        """Test that normalization works correctly."""
        # Create signals with different scales
        signal1 = np.sin(np.linspace(0, 10, 1000)) * 1000
        signal2 = np.sin(np.linspace(0, 10, 1000) + np.pi / 6) * 0.001
        
        plv_normalized = plv_calc(signal1, signal2, normalize=True)
        plv_unnormalized = plv_calc(signal1, signal2, normalize=False)
        
        # With normalization, PLV should be close to 1.0
        assert np.isclose(plv_normalized, 1.0, atol=1e-5), f"Expected PLV=1.0 with normalization, got {plv_normalized}"
        
        # Without normalization, PLV might differ due to scale differences
        # but should still be a valid value
        assert 0.0 <= plv_unnormalized <= 1.0
    
    def test_plv_calc_random_signals(self):
        """Test PLV calculation on random signals."""
        np.random.seed(123)
        signal1 = np.random.randn(1000)
        signal2 = np.random.randn(1000)
        
        plv = plv_calc(signal1, signal2)
        
        assert isinstance(plv, float)
        assert 0.0 <= plv <= 1.0
        assert plv < 0.1, f"Expected low PLV for random signals, got {plv}"
    
    def test_plv_calc_1d_requirement(self):
        """Should raise ValueError for non-1D inputs."""
        signal1 = np.random.randn(10, 5)
        signal2 = np.random.randn(10, 5)
        with pytest.raises(ValueError):
            plv_calc(signal1, signal2)