"""
Unit tests for the QuantumState entity class.
"""

import pytest
import numpy as np
from scipy import sparse

from models.quantum_state import (
    QuantumState,
    QuantumStateError
)


class TestQuantumStateInit:
    """Tests for QuantumState initialization."""

    def test_init_dense_valid(self):
        """Test initialization with valid dense data."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        assert state.num_qubits == 2
        assert state.dimension == 4
        assert not state.is_sparse

    def test_init_sparse_valid(self):
        """Test initialization with valid sparse data."""
        psi = sparse.csr_matrix(np.array([1, 0, 0, 0], dtype=complex))
        state = QuantumState(psi, num_qubits=2)
        assert state.num_qubits == 2
        assert state.dimension == 4
        assert state.is_sparse

    def test_init_num_qubits_inferred(self):
        """Test that num_qubits is inferred when not provided."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi)
        assert state.num_qubits == 2

    def test_init_num_qubits_inference_failure(self):
        """Test that non-power-of-2 dimension is handled."""
        psi = np.array([1, 0, 0], dtype=complex)
        # Should not raise, but warn and set num_qubits to None
        state = QuantumState(psi)
        assert state.num_qubits is None

    def test_init_dimension_mismatch(self):
        """Test that dimension mismatch raises error."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        with pytest.raises(QuantumStateError):
            QuantumState(psi, num_qubits=3)  # 3 qubits -> 8 dim

    def test_init_none_data(self):
        """Test that None data raises error."""
        with pytest.raises(QuantumStateError):
            QuantumState(None)

    def test_init_multidimensional_array(self):
        """Test that multi-dimensional arrays are flattened."""
        psi = np.array([[1, 0], [0, 0]], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        assert state.dimension == 4
        assert state.to_dense().shape == (4,)


class TestQuantumStateConversion:
    """Tests for data format conversion."""

    def test_to_dense_from_dense(self):
        """Test converting dense to dense."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        result = state.to_dense()
        np.testing.assert_array_equal(result, psi)

    def test_to_dense_from_sparse(self):
        """Test converting sparse to dense."""
        psi = sparse.csr_matrix(np.array([1, 0, 0, 0], dtype=complex))
        state = QuantumState(psi, num_qubits=2)
        result = state.to_dense()
        expected = np.array([1, 0, 0, 0], dtype=complex)
        np.testing.assert_array_equal(result, expected)

    def test_to_sparse_from_dense(self):
        """Test converting dense to sparse."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        result = state.to_sparse()
        assert sparse.issparse(result)
        np.testing.assert_array_equal(result.toarray().flatten(), psi)

    def test_to_sparse_from_sparse(self):
        """Test converting sparse to sparse."""
        psi = sparse.csr_matrix(np.array([1, 0, 0, 0], dtype=complex))
        state = QuantumState(psi, num_qubits=2)
        result = state.to_sparse()
        assert sparse.issparse(result)

    def test_to_sparse_format_csc(self):
        """Test converting to CSC format."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        result = state.to_sparse(format='csc')
        assert isinstance(result, sparse.csc_matrix)

    def test_to_sparse_format_invalid(self):
        """Test that invalid format raises error."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        with pytest.raises(QuantumStateError):
            state.to_sparse(format='invalid')


class TestQuantumStateProperties:
    """Tests for state properties and methods."""

    def test_entanglement_entropy_bell_state(self):
        """Test entanglement entropy for a Bell state."""
        psi = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        state = QuantumState(psi, num_qubits=2)
        # Entropy for qubit 0 should be ln(2)
        entropy = state.entanglement_entropy((0,))
        assert np.isclose(entropy, np.log(2))

    def test_entanglement_entropy_product_state(self):
        """Test entanglement entropy for a product state."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        # Product state should have zero entropy
        entropy = state.entanglement_entropy((0,))
        assert np.isclose(entropy, 0.0)

    def test_entanglement_entropy_invalid_subsystem(self):
        """Test that invalid subsystem raises error."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        with pytest.raises(QuantumStateError):
            state.entanglement_entropy((2,))  # Invalid index

    def test_get_reduced_density_matrix(self):
        """Test reduced density matrix computation."""
        # Bell state
        psi = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        state = QuantumState(psi, num_qubits=2)
        rho_red = state.get_reduced_density_matrix((0,))
        # Should be maximally mixed: I/2
        expected = np.eye(2) / 2
        np.testing.assert_array_almost_equal(rho_red, expected)

    def test_copy(self):
        """Test state copying."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state = QuantumState(psi, num_qubits=2)
        state_copy = state.copy()
        assert state.dimension == state_copy.dimension
        assert state.num_qubits == state_copy.num_qubits
        assert not np.shares_memory(state.to_dense(), state_copy.to_dense())

    def test_eq_same_state(self):
        """Test equality for identical states."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state1 = QuantumState(psi, num_qubits=2)
        state2 = QuantumState(psi.copy(), num_qubits=2)
        assert state1 == state2

    def test_eq_different_state(self):
        """Test inequality for different states."""
        state1 = QuantumState(np.array([1, 0, 0, 0], dtype=complex), num_qubits=2)
        state2 = QuantumState(np.array([0, 1, 0, 0], dtype=complex), num_qubits=2)
        assert state1 != state2

    def test_eq_different_format(self):
        """Test equality between dense and sparse representations."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        state_dense = QuantumState(psi, num_qubits=2)
        state_sparse = QuantumState(
            sparse.csr_matrix(psi),
            num_qubits=2
        )
        assert state_dense == state_sparse


class TestQuantumStateGeneration:
    """Tests for static state generation methods."""

    def test_generate_random(self):
        """Test random state generation."""
        state = QuantumState.generate_random(num_qubits=2)
        assert state.num_qubits == 2
        assert state.dimension == 4
        # Check normalization
        norm = np.vdot(state.to_dense(), state.to_dense()).real
        assert np.isclose(norm, 1.0)

    def test_generate_random_seed(self):
        """Test random state generation with seed."""
        state1 = QuantumState.generate_random(num_qubits=2, seed=42)
        state2 = QuantumState.generate_random(num_qubits=2, seed=42)
        np.testing.assert_array_equal(state1.to_dense(), state2.to_dense())

    def test_generate_product_state(self):
        """Test product state generation."""
        state = QuantumState.generate_product_state(num_qubits=2)
        assert state.num_qubits == 2
        # Product state should have zero entanglement
        entropy = state.entanglement_entropy((0,))
        assert np.isclose(entropy, 0.0)

    def test_generate_ghz_state(self):
        """Test GHZ state generation."""
        state = QuantumState.generate_ghz_state(num_qubits=3)
        assert state.num_qubits == 3
        # GHZ state: (|000> + |111>) / sqrt(2)
        psi = state.to_dense()
        assert np.isclose(np.abs(psi[0]), 1.0 / np.sqrt(2))
        assert np.isclose(np.abs(psi[-1]), 1.0 / np.sqrt(2))

    def test_generate_w_state(self):
        """Test W state generation."""
        state = QuantumState.generate_w_state(num_qubits=3)
        assert state.num_qubits == 3
        # W state has equal amplitude on single-excitation states
        psi = state.to_dense()
        # Positions 1, 2, 4 should have equal amplitude
        expected_amp = 1.0 / np.sqrt(3)
        assert np.isclose(np.abs(psi[1]), expected_amp)
        assert np.isclose(np.abs(psi[2]), expected_amp)
        assert np.isclose(np.abs(psi[4]), expected_amp)

    def test_generate_bell_state_phi_plus(self):
        """Test Bell state phi+ generation."""
        state = QuantumState.generate_bell_state('phi_plus')
        assert state.num_qubits == 2
        psi = state.to_dense()
        expected = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(psi, expected)

    def test_generate_bell_state_invalid(self):
        """Test that invalid Bell state type raises error."""
        with pytest.raises(QuantumStateError):
            QuantumState.generate_bell_state('invalid')


class TestQuantumStateHDF5:
    """Tests for HDF5 I/O."""

    def test_to_hdf5_and_from_hdf5(self, tmp_path):
        """Test saving and loading from HDF5."""
        psi = np.array([1, 0, 0, 0], dtype=complex)
        original = QuantumState(psi, num_qubits=2)

        filepath = tmp_path / "test_state.h5"
        original.to_hdf5(str(filepath), 'wavefunction')

        loaded = QuantumState.from_hdf5(str(filepath), 'wavefunction')
        assert loaded.num_qubits == original.num_qubits
        np.testing.assert_array_almost_equal(
            loaded.to_dense(),
            original.to_dense()
        )

    def test_from_hdf5_missing_dataset(self, tmp_path):
        """Test that missing dataset raises error."""
        filepath = tmp_path / "test.h5"
        filepath.touch()  # Create empty file

        with pytest.raises(QuantumStateError):
            QuantumState.from_hdf5(str(filepath), 'nonexistent')