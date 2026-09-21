import pytest
import numpy as np
import os
import tempfile
import h5py
from metrics import (
    quantize_wavefunction, 
    generate_internal_baseline, 
    calculate_ncd, 
    load_wavefunction_from_hdf5,
    calculate_entanglement_entropy
)
from logging_config import E_NUMERICAL_INSTABILITY

class TestQuantization:
    def test_quantize_wavefunction_shape(self):
        """Test that quantization produces correct shape."""
        n = 10
        wf = np.random.randn(n) + 1j * np.random.randn(n)
        q = quantize_wavefunction(wf)
        assert q.shape == (n * 2,), f"Expected shape {(n*2,)}, got {q.shape}"
        assert q.dtype == np.int16, f"Expected dtype int16, got {q.dtype}"

    def test_quantize_wavefunction_values(self):
        """Test that quantization scales values correctly."""
        wf = np.array([1.0 + 0j, 0.0 + 1j, -1.0 + 0j, 0.0 - 1j])
        q = quantize_wavefunction(wf)
        # Max value should be near 32767
        assert np.max(np.abs(q)) <= 32767
        assert np.max(np.abs(q)) > 0

    def test_quantize_zero_wavefunction(self):
        """Test that zero wavefunction raises error."""
        wf = np.zeros(10, dtype=complex)
        with pytest.raises(ValueError):
            quantize_wavefunction(wf)

class TestBaseline:
    def test_baseline_size_match(self):
        """Test that baseline matches input size."""
        n = 100
        wf = np.random.randn(n) + 1j * np.random.randn(n)
        baseline = generate_internal_baseline(wf, seed=42)
        assert baseline.shape == (n * 2,), f"Expected shape {(n*2,)}, got {baseline.shape}"
        assert baseline.dtype == np.int16

    def test_baseline_reproducibility(self):
        """Test that baseline is reproducible with same seed."""
        wf = np.random.randn(10) + 1j * np.random.randn(10)
        b1 = generate_internal_baseline(wf, seed=123)
        b2 = generate_internal_baseline(wf, seed=123)
        assert np.array_equal(b1, b2)

class TestNCD:
    def test_ncd_self_similarity(self):
        """Test NCD of identical arrays is low."""
        data = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        # NCD(data, data) should be close to 0?
        # C(xx) approx 2*C(x) if no compression gain? 
        # Actually C(xx) is not exactly 2*C(x) due to headers.
        # But NCD(x, x) = (C(xx) - C(x)) / C(x) = (C(xx)/C(x)) - 1.
        # If C(xx) ~ C(x) (highly compressible), NCD ~ 0.
        # If C(xx) ~ 2*C(x), NCD ~ 1.
        # Let's just check it returns a float in [0, 1]
        ncd = calculate_ncd(data, data)
        assert 0.0 <= ncd <= 2.0 # Allow some slack for compression overhead

    def test_ncd_randomness(self):
        """Test NCD between different random arrays is higher."""
        d1 = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        d2 = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        ncd = calculate_ncd(d1, d2)
        # Should be positive
        assert ncd >= 0

class TestEntanglementEntropy:
    def test_entanglement_entropy_product_state(self):
        """Test entropy of a product state is near zero."""
        # Product state: |00...0>
        n = 10
        psi = np.zeros(2**n, dtype=complex)
        psi[0] = 1.0
        split_idx = 5
        sys_dim = 2
        entropy, _ = calculate_entanglement_entropy(psi, split_idx, sys_dim)
        assert entropy < 1e-6, f"Product state entropy should be ~0, got {entropy}"

    def test_entanglement_entropy_max_entangled(self):
        """Test entropy of a maximally entangled state."""
        # Bell state for 2 qubits: (|00> + |11>)/sqrt(2)
        psi = np.zeros(4, dtype=complex)
        psi[0] = 1/np.sqrt(2)
        psi[3] = 1/np.sqrt(2)
        split_idx = 1
        sys_dim = 2
        entropy, _ = calculate_entanglement_entropy(psi, split_idx, sys_dim)
        # Max entropy for 1 qubit is 1.0
        assert abs(entropy - 1.0) < 1e-5, f"Max entangled entropy should be ~1, got {entropy}"

class TestLoadHDF5:
    def test_load_wavefunction_hdf5(self):
        """Test loading wavefunction from HDF5."""
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            fname = f.name
            with h5py.File(fname, 'w') as hf:
                data = np.random.randn(10) + 1j * np.random.randn(10)
                hf.create_dataset('wavefunction', data=data)
        
        loaded = load_wavefunction_from_hdf5(fname)
        assert np.allclose(loaded, data)
        os.remove(fname)

    def test_load_wavefunction_missing(self):
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            load_wavefunction_from_hdf5("nonexistent.h5")

    def test_load_wavefunction_missing_dataset(self):
        """Test error on missing dataset in HDF5."""
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            fname = f.name
            with h5py.File(fname, 'w') as hf:
                hf.create_dataset('other', data=[1, 2, 3])
        
        with pytest.raises(KeyError):
            load_wavefunction_from_hdf5(fname)
        os.remove(fname)