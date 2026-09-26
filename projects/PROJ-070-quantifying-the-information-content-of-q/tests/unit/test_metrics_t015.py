"""
Unit tests for T015: Entanglement Entropy Calculation.

Tests the calculate_entanglement_entropy function and related helpers.
"""
import pytest
import numpy as np
import os
import sys
import tempfile
import h5py

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code')))

from metrics import calculate_entanglement_entropy, load_wavefunction_from_hdf5, E_DATA_INSUFFICIENT
from scipy.sparse.linalg import svds
from scipy.sparse import csr_matrix

class TestEntanglementEntropy:
    
    def test_maximally_entangled_state(self):
        """
        Test with a known maximally entangled state (Bell state for N=2).
        |psi> = (|00> + |11>) / sqrt(2)
        Coefficients: [1/sqrt(2), 0, 0, 1/sqrt(2)]
        Cut at N=1 (2x2 matrix).
        Expected Entropy: ln(2) ~ 0.693
        """
        N = 2
        cut = 1
        coeffs = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
        
        entropy = calculate_entanglement_entropy(coeffs, N, cut)
        
        expected = np.log(2)
        assert np.isclose(entropy, expected, atol=1e-4), f"Expected {expected}, got {entropy}"
        
    def test_product_state(self):
        """
        Test with a product state (no entanglement).
        |psi> = |00>
        Coefficients: [1, 0, 0, 0]
        Expected Entropy: 0
        """
        N = 2
        cut = 1
        coeffs = np.array([1.0, 0, 0, 0])
        
        entropy = calculate_entanglement_entropy(coeffs, N, cut)
        
        assert np.isclose(entropy, 0.0, atol=1e-6), f"Expected 0, got {entropy}"

    def test_larger_system_sparse_svd(self):
        """
        Test a larger system (N=10) to ensure sparse SVD path is taken.
        Create a random state and verify it runs without error.
        """
        N = 10
        cut = 5
        dim = 2 ** N
        # Random normalized state
        coeffs = np.random.randn(dim) + 1j * np.random.randn(dim)
        coeffs = coeffs / np.linalg.norm(coeffs)
        
        entropy = calculate_entanglement_entropy(coeffs, N, cut)
        
        assert entropy > 0, "Random state should have positive entropy"
        assert entropy <= np.log(2 ** min(cut, N-cut)), "Entropy cannot exceed max possible"

    def test_nan_input_raises(self):
        """
        Test that NaN input raises E_DATA_INSUFFICIENT.
        """
        N = 2
        cut = 1
        coeffs = np.array([1.0, np.nan, 0, 0])
        
        with pytest.raises(E_DATA_INSUFFICIENT):
            calculate_entanglement_entropy(coeffs, N, cut)

    def test_small_system_fallback(self):
        """
        Test system where svds k < min_dim might be tricky, 
        ensuring fallback logic (if any) or correct k selection works.
        N=1, cut=1 -> dim 2x1. min=1. k must be < 1 -> k=0?
        svds(k=0) is invalid.
        The implementation should handle min_dim=1 gracefully.
        """
        N = 1
        cut = 1
        coeffs = np.array([1.0, 0.0]) # |0>
        
        # This should not crash. Entropy should be 0.
        entropy = calculate_entanglement_entropy(coeffs, N, cut)
        assert np.isclose(entropy, 0.0, atol=1e-6)

class TestLoadWavefunction:
    
    def test_load_hdf5(self):
        """Test loading wavefunction from HDF5."""
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            with h5py.File(tmp.name, 'w') as f:
                f.create_dataset('wavefunction', data=np.array([1.0, 0, 0, 0]))
                f.attrs['system_size'] = 2
                f.attrs['state_id'] = 'test_state'
                f.attrs['cut_position'] = 1
            
            coeffs, meta = load_wavefunction_from_hdf5(tmp.name)
            
            assert np.allclose(coeffs, [1.0, 0, 0, 0])
            assert meta['system_size'] == 2
            assert meta['state_id'] == 'test_state'
            os.unlink(tmp.name)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
