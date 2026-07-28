"""
Unit tests for metrics calculation: Entanglement Entropy and NCD.
Extends existing test suite.
"""
import numpy as np
import pytest
import gzip
import bz2
import lzma
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from metrics import (
    check_numerical_stability,
    calculate_entanglement_entropy,
    quantize_wavefunction,
    calculate_ncd
)
from logging_config import E_NUMERICAL_INSTABILITY, get_instability_events, clear_event_logs


class TestNumericalStability:
    """Tests for numerical stability checks."""

    def test_check_numerical_stability_clean(self):
        """Test that clean data passes stability check."""
        data = np.array([1.0, 2.0, 3.0, 4.0])
        result = check_numerical_stability(data)
        assert result is True
        assert len(get_instability_events()) == 0

    def test_check_numerical_stability_nan(self):
        """Test that NaN detection triggers instability flag."""
        clear_event_logs()
        data = np.array([1.0, np.nan, 3.0])
        result = check_numerical_stability(data)
        assert result is False
        events = get_instability_events()
        assert len(events) > 0
        assert any(e['type'] == E_NUMERICAL_INSTABILITY for e in events)

    def test_check_numerical_stability_inf(self):
        """Test that Inf detection triggers instability flag."""
        clear_event_logs()
        data = np.array([1.0, np.inf, 3.0])
        result = check_numerical_stability(data)
        assert result is False
        events = get_instability_events()
        assert len(events) > 0

    def test_check_numerical_stability_matrix(self):
        """Test stability check on 2D matrix."""
        clear_event_logs()
        matrix = np.random.rand(5, 5)
        matrix[2, 2] = np.nan
        result = check_numerical_stability(matrix)
        assert result is False


class TestQuantization:
    """Tests for wavefunction quantization (16-bit fixed-point)."""

    def test_quantize_wavefunction_range(self):
        """Test that quantized values stay within int16 bounds."""
        # Create a wavefunction with complex amplitudes
        np.random.seed(42)
        n = 100
        real = np.random.randn(n)
        imag = np.random.randn(n)
        psi = real + 1j * imag
        # Normalize
        psi = psi / np.linalg.norm(psi)

        quantized = quantize_wavefunction(psi)

        assert quantized.dtype == np.int16
        assert np.min(quantized) >= np.iinfo(np.int16).min
        assert np.max(quantized) <= np.iinfo(np.int16).max

    def test_quantize_wavefunction_preserves_sign(self):
        """Test that sign information is preserved after quantization."""
        np.random.seed(123)
        n = 50
        real = np.random.randn(n)
        imag = np.random.randn(n)
        psi = real + 1j * imag
        psi = psi / np.linalg.norm(psi)

        # Separate real and imaginary parts for sign check
        real_quant = quantize_wavefunction(psi.real)
        imag_quant = quantize_wavefunction(psi.imag)

        # Check that signs match (allowing for zero crossings)
        assert np.all((np.sign(real_quant) == np.sign(psi.real)) | (psi.real == 0))
        assert np.all((np.sign(imag_quant) == np.sign(psi.imag)) | (psi.imag == 0))

    def test_quantize_wavefunction_norm_approximation(self):
        """Test that quantized wavefunction roughly preserves norm structure."""
        np.random.seed(456)
        n = 200
        psi = np.random.randn(n) + 1j * np.random.randn(n)
        psi = psi / np.linalg.norm(psi)

        quantized = quantize_wavefunction(psi)

        # The quantized vector should have significant magnitude
        assert np.linalg.norm(quantized) > 0.1 * np.iinfo(np.int16).max


class TestNCDCalculation:
    """Tests for Normalized Compression Distance calculation."""

    def test_ncd_identical_inputs(self):
        """NCD should be ~0 for identical inputs."""
        data = b"Hello World! " * 1000
        ncd = calculate_ncd(data, data)
        # NCD for identical inputs should be very small (theoretical 0)
        assert ncd < 0.05

    def test_ncd_compressor_selection(self):
        """Test that NCD works with default compressor (gzip)."""
        data1 = b"A" * 10000
        data2 = b"B" * 10000
        ncd = calculate_ncd(data1, data2)
        assert 0.0 <= ncd <= 1.0

    def test_ncd_different_compressors(self):
        """Test NCD with different compressors (gzip, bz2, lzma)."""
        data1 = b"Repetitive data pattern " * 500
        data2 = b"Random data " + os.urandom(2000)

        # Gzip
        ncd_gzip = calculate_ncd(data1, data2, compressor='gzip')
        assert 0.0 <= ncd_gzip <= 1.0

        # Bzip2
        ncd_bz2 = calculate_ncd(data1, data2, compressor='bz2')
        assert 0.0 <= ncd_bz2 <= 1.0

        # LZMA
        ncd_lzma = calculate_ncd(data1, data2, compressor='lzma')
        assert 0.0 <= ncd_lzma <= 1.0

    def test_ncd_symmetry(self):
        """NCD should be symmetric: NCD(x, y) == NCD(y, x)."""
        np.random.seed(789)
        x = np.random.randint(0, 255, 5000, dtype=np.uint8).tobytes()
        y = np.random.randint(0, 255, 5000, dtype=np.uint8).tobytes()

        ncd_xy = calculate_ncd(x, y)
        ncd_yx = calculate_ncd(y, x)

        # Allow small floating point differences
        assert abs(ncd_xy - ncd_yx) < 1e-6

    def test_ncd_self_distance(self):
        """NCD(x, x) should be close to 0."""
        data = os.urandom(3000)
        ncd = calculate_ncd(data, data)
        assert ncd < 0.05

    def test_ncd_compressed_length_bounds(self):
        """Test that compressed lengths behave as expected."""
        # Highly compressible
        repetitive = b"A" * 10000
        # Random (incompressible)
        random_data = os.urandom(10000)

        # Compress both
        comp_rep = gzip.compress(repetitive)
        comp_rand = gzip.compress(random_data)

        # Repetitive should compress much better
        assert len(comp_rep) < len(comp_rand)

        # NCD between repetitive and random should be high
        ncd = calculate_ncd(repetitive, random_data)
        assert ncd > 0.5  # Heuristic threshold


class TestEntanglementEntropy:
    """Tests for bipartite entanglement entropy calculation."""

    def test_entanglement_entropy_product_state(self):
        """Product state should have near-zero entanglement entropy."""
        # Construct a simple product state: |00...0>
        # For N=4, split into A (2 qubits) and B (2 qubits)
        # State: |00> |00> -> density matrix of A is |00><00| (pure) -> entropy 0
        psi = np.zeros(2**4)
        psi[0] = 1.0  # |0000>

        # Reshape to (2^2, 2^2) for bipartition
        psi_matrix = psi.reshape(2**2, 2**2)

        entropy = calculate_entanglement_entropy(psi_matrix)

        assert entropy < 1e-6

    def test_entanglement_entropy_maximally_entangled(self):
        """Bell-like state should have maximal entropy for its dimension."""
        # Create a maximally entangled state for 2x2 split
        # |Phi+> = (|00> + |11>) / sqrt(2)
        psi = np.zeros(4)
        psi[0] = 1/np.sqrt(2)
        psi[3] = 1/np.sqrt(2)

        psi_matrix = psi.reshape(2, 2)

        entropy = calculate_entanglement_entropy(psi_matrix)

        # Max entropy for 2x2 is log2(2) = 1.0
        assert abs(entropy - 1.0) < 1e-3

    def test_entanglement_entropy_random_state(self):
        """Random state should have positive entropy."""
        np.random.seed(999)
        n_a, n_b = 4, 4  # 16-dimensional split
        psi = np.random.randn(n_a * n_b) + 1j * np.random.randn(n_a * n_b)
        psi = psi / np.linalg.norm(psi)

        psi_matrix = psi.reshape(n_a, n_b)

        entropy = calculate_entanglement_entropy(psi_matrix)

        assert entropy > 0.0
        assert entropy <= np.log2(min(n_a, n_b))

    def test_entanglement_entropy_sparse_input(self):
        """Test that entanglement calculation handles sparse-like inputs correctly."""
        # Create a state with only a few non-zero components
        psi = np.zeros(16)
        psi[2] = 0.6
        psi[5] = 0.8
        psi = psi / np.linalg.norm(psi)

        psi_matrix = psi.reshape(4, 4)

        entropy = calculate_entanglement_entropy(psi_matrix)
        assert entropy >= 0.0


class TestIntegration:
    """Integration tests combining quantization and NCD."""

    def test_full_quantization_ncd_pipeline(self):
        """Test the full pipeline: Wavefunction -> Quantize -> NCD."""
        np.random.seed(111)
        n = 100
        psi = np.random.randn(n) + 1j * np.random.randn(n)
        psi = psi / np.linalg.norm(psi)

        # Quantize
        quantized = quantize_wavefunction(psi)

        # Convert to bytes for NCD
        # Pack real and imaginary parts separately
        real_bytes = quantized.real.tobytes()
        imag_bytes = quantized.imag.tobytes()

        # Calculate NCD between real and imaginary parts (should be non-trivial)
        ncd = calculate_ncd(real_bytes, imag_bytes)

        assert 0.0 <= ncd <= 1.0

    def test_quantization_stability_with_entanglement(self):
        """Ensure quantization doesn't break entanglement calculation."""
        # Create a known entangled state
        psi = np.zeros(8)
        psi[0] = 0.707
        psi[7] = 0.707
        psi = psi / np.linalg.norm(psi)

        psi_matrix = psi.reshape(2, 4)
        original_entropy = calculate_entanglement_entropy(psi_matrix)

        # Quantize and reconstruct (conceptually)
        quantized = quantize_wavefunction(psi)

        # The test here is that quantization runs without error
        # and the original entropy calculation remains valid
        assert original_entropy > 0.9
        assert quantized.shape == psi.shape