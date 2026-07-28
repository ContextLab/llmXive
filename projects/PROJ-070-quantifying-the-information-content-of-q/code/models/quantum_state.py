"""
QuantumState entity class supporting sparse representation.

This module defines the core `QuantumState` entity used throughout the pipeline.
It supports both dense (numpy array) and sparse (scipy.sparse) representations
of wavefunctions, with automatic conversion and validation.
"""

import numpy as np
from scipy import sparse
from typing import Optional, Union, Tuple, Dict, Any

from logging_config import logger


class QuantumStateError(Exception):
    """Custom exception for QuantumState operations."""
    pass


class QuantumState:
    """
    Represents a quantum many-body state vector.

    Supports both dense and sparse representations internally.
    Automatically handles conversion between formats as needed.

    Attributes:
        data (np.ndarray | sparse.csr_matrix): The state vector data.
        num_qubits (int): Number of qubits/spins in the system.
        is_sparse (bool): True if stored in sparse format.
    """

    def __init__(
        self,
        data: Union[np.ndarray, sparse.spmatrix],
        num_qubits: Optional[int] = None,
        validate: bool = True
    ):
        """
        Initialize a QuantumState.

        Args:
            data: State vector as dense numpy array or sparse matrix.
            num_qubits: Explicit number of qubits. If None, inferred from data size.
            validate: If True, perform validation checks.

        Raises:
            QuantumStateError: If data is invalid or dimensions mismatch.
        """
        self._data: Union[np.ndarray, sparse.spmatrix] = None
        self._num_qubits: int = num_qubits
        self._is_sparse: bool = False

        if data is None:
            raise QuantumStateError("Data cannot be None")

        # Handle sparse input
        if sparse.issparse(data):
            # Ensure it's a 1D vector (compressed)
            if data.ndim == 2:
                if data.shape[0] == 1:
                    data = data.toarray().flatten()
                elif data.shape[1] == 1:
                    data = data.toarray().flatten()
                else:
                    raise QuantumStateError(
                        f"Sparse input must be 1D vector or (1, N)/(N, 1) matrix, "
                        f"got shape {data.shape}"
                    )
            self._data = sparse.csr_matrix(data)
            self._is_sparse = True
        else:
            # Dense numpy array
            data = np.asarray(data)
            if data.ndim > 1:
                data = data.flatten()
            self._data = data
            self._is_sparse = False

        # Infer or validate num_qubits
        dim = self._data.shape[0]
        if self._num_qubits is None:
            # Check if dim is a power of 2
            if dim > 0 and (dim & (dim - 1)) == 0:
                self._num_qubits = int(np.log2(dim))
            else:
                logger.warning(
                    f"Dimension {dim} is not a power of 2. "
                    "Setting num_qubits to None."
                )
                self._num_qubits = None
        else:
            expected_dim = 2 ** self._num_qubits
            if dim != expected_dim:
                raise QuantumStateError(
                    f"Dimension mismatch: data has {dim} elements, "
                    f"but num_qubits={self._num_qubits} implies {expected_dim}"
                )

        if validate:
            self._validate()

    @property
    def data(self) -> Union[np.ndarray, sparse.spmatrix]:
        """Get the raw data (dense or sparse)."""
        return self._data

    @property
    def num_qubits(self) -> Optional[int]:
        """Get the number of qubits."""
        return self._num_qubits

    @property
    def dimension(self) -> int:
        """Get the Hilbert space dimension (2^num_qubits)."""
        return self._data.shape[0]

    @property
    def is_sparse(self) -> bool:
        """Check if data is stored in sparse format."""
        return self._is_sparse

    def _validate(self) -> None:
        """Validate the state vector (normalization, NaN/Inf)."""
        data = self._data
        if sparse.issparse(data):
            # For sparse, compute norm via sum of squares
            norm_sq = data.dot(data.conj()).toarray().flatten()[0]
        else:
            norm_sq = np.vdot(data, data).real

        # Check for NaN/Inf in norm
        if not np.isfinite(norm_sq):
            raise QuantumStateError(f"Invalid norm: {norm_sq} (contains NaN/Inf)")

        # Warn if not normalized (within tolerance)
        if not np.isclose(norm_sq, 1.0, atol=1e-6):
            logger.warning(
                f"State is not normalized (norm^2 = {norm_sq:.6f}). "
                "Normalization is assumed for most calculations."
            )

    def to_dense(self) -> np.ndarray:
        """Convert to dense numpy array."""
        if self._is_sparse:
            self._data = self._data.toarray().flatten()
            self._is_sparse = False
        return self._data

    def to_sparse(self, format: str = 'csr') -> sparse.spmatrix:
        """Convert to sparse matrix in specified format."""
        if not self._is_sparse:
            if self._data.ndim == 1:
                self._data = sparse.csr_matrix(self._data)
            else:
                self._data = sparse.csr_matrix(self._data.flatten())
            self._is_sparse = True

        if format == 'csr':
            return self._data.tocsr()
        elif format == 'csc':
            return self._data.tocsc()
        elif format == 'coo':
            return self._data.tocoo()
        else:
            raise QuantumStateError(f"Unsupported sparse format: {format}")

    def get_reduced_density_matrix(self, subsystem: Tuple[int, ...]) -> np.ndarray:
        """
        Compute the reduced density matrix for a given subsystem.

        Args:
            subsystem: Tuple of qubit indices to keep (0-indexed).

        Returns:
            Dense reduced density matrix.

        Note:
            This always returns a dense matrix as the reduced density
            matrix is typically not sparse for entangled states.
        """
        if self._num_qubits is None:
            raise QuantumStateError("Cannot compute RDM: num_qubits is not set")

        all_qubits = set(range(self._num_qubits))
        subsystem_set = set(subsystem)

        if not subsystem_set.issubset(all_qubits):
            raise QuantumStateError(
                f"Invalid subsystem indices: {subsystem}. "
                f"Valid indices are 0 to {self._num_qubits - 1}"
            )

        # Get full density matrix (dense)
        psi = self.to_dense()
        rho_full = np.outer(psi, psi.conj())

        # Reshape to (2, 2, ..., 2) tensor
        n_qubits = self._num_qubits
        shape = [2] * n_qubits
        rho_tensor = rho_full.reshape(shape + shape)

        # Trace out complement subsystem
        # Indices to trace over (complement of subsystem)
        trace_indices = sorted(all_qubits - subsystem_set)

        # Number of qubits to keep
        n_keep = len(subsystem)
        n_trace = len(trace_indices)

        # Reshape to separate kept and traced indices
        # Current shape: (d1, d2, ..., dn, d1, d2, ..., dn)
        # We want to trace over specific pairs

        # Build permutation to group kept and traced indices
        # Keep indices: first half of tensor, trace indices: second half
        kept_indices = list(subsystem)

        # Permute to group kept indices together, then traced
        # New order: [kept...] [traced...] [kept...] [traced...]
        new_order = kept_indices + trace_indices + [
            n_qubits + i for i in kept_indices
        ] + [n_qubits + i for i in trace_indices]

        rho_perm = np.transpose(rho_tensor, new_order)

        # Reshape to (2^k, 2^k, 2^t) where k=kept, t=traced
        kept_dim = 2 ** n_keep
        traced_dim = 2 ** n_trace

        rho_reshaped = rho_perm.reshape(kept_dim, kept_dim, traced_dim)

        # Trace over the last axis
        rho_reduced = np.trace(rho_reshaped, axis1=0, axis2=2)

        return rho_reduced

    def entanglement_entropy(self, subsystem: Tuple[int, ...]) -> float:
        """
        Compute the von Neumann entanglement entropy for a subsystem.

        Args:
            subsystem: Tuple of qubit indices defining the subsystem.

        Returns:
            Entanglement entropy in nats.
        """
        rho_red = self.get_reduced_density_matrix(subsystem)

        # Compute eigenvalues of reduced density matrix
        eigenvalues = np.linalg.eigvalsh(rho_red)

        # Filter out zero/negative eigenvalues (numerical noise)
        eigenvalues = eigenvalues[eigenvalues > 1e-15]

        # Compute entropy: -sum(p * log(p))
        entropy = -np.sum(eigenvalues * np.log(eigenvalues))

        return entropy

    def __repr__(self) -> str:
        sparse_str = "sparse" if self._is_sparse else "dense"
        qubits_str = str(self._num_qubits) if self._num_qubits else "unknown"
        return (
            f"QuantumState(dimension={self.dimension}, "
            f"num_qubits={qubits_str}, format={sparse_str})"
        )

    def __eq__(self, other: 'QuantumState') -> bool:
        if not isinstance(other, QuantumState):
            return False
        if self.dimension != other.dimension:
            return False
        # Compare data (handle sparse vs dense)
        if sparse.issparse(self._data) and sparse.issparse(other._data):
            return np.allclose(
                self._data.toarray().flatten(),
                other._data.toarray().flatten()
            )
        elif not sparse.issparse(self._data) and not sparse.issparse(other._data):
            return np.allclose(self._data, other._data)
        else:
            # Mixed formats
            return np.allclose(
                self.to_dense(),
                other.to_dense()
            )

    def copy(self) -> 'QuantumState':
        """Create a deep copy of this state."""
        new_data = self._data.copy()
        return QuantumState(new_data, self._num_qubits, validate=False)

    @classmethod
    def from_hdf5(cls, filepath: str, dataset_name: str = 'wavefunction') -> 'QuantumState':
        """
        Load a QuantumState from an HDF5 file.

        Args:
            filepath: Path to the HDF5 file.
            dataset_name: Name of the dataset within the file.

        Returns:
            Loaded QuantumState instance.
        """
        import h5py

        with h5py.File(filepath, 'r') as f:
            if dataset_name not in f:
                raise QuantumStateError(
                    f"Dataset '{dataset_name}' not found in {filepath}"
                )
            data = f[dataset_name][()]
            num_qubits = f.attrs.get('num_qubits', None)

        return cls(data, num_qubits=num_qubits)

    def to_hdf5(self, filepath: str, dataset_name: str = 'wavefunction') -> None:
        """
        Save the QuantumState to an HDF5 file.

        Args:
            filepath: Path to the HDF5 file.
            dataset_name: Name of the dataset within the file.
        """
        import h5py

        with h5py.File(filepath, 'w') as f:
            # Store data
            f.create_dataset(dataset_name, data=self.to_dense())
            # Store metadata
            if self._num_qubits is not None:
                f.attrs['num_qubits'] = self._num_qubits
            f.attrs['format'] = 'dense'  # Always save as dense for compatibility

    @staticmethod
    def generate_random(num_qubits: int, seed: Optional[int] = None) -> 'QuantumState':
        """
        Generate a random Haar-distributed quantum state.

        Args:
            num_qubits: Number of qubits.
            seed: Random seed for reproducibility.

        Returns:
            Random QuantumState.
        """
        if seed is not None:
            np.random.seed(seed)

        dim = 2 ** num_qubits
        # Generate complex Gaussian random vector
        real_part = np.random.randn(dim)
        imag_part = np.random.randn(dim)
        psi = real_part + 1j * imag_part

        # Normalize
        psi = psi / np.linalg.norm(psi)

        return QuantumState(psi, num_qubits=num_qubits, validate=True)

    @staticmethod
    def generate_product_state(
        num_qubits: int,
        phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None
    ) -> 'QuantumState':
        """
        Generate a product state (no entanglement).

        Args:
            num_qubits: Number of qubits.
            phases: Optional array of phases for each qubit (default: 0).
            seed: Random seed for reproducibility.

        Returns:
            Product state QuantumState.
        """
        if seed is not None:
            np.random.seed(seed)

        if phases is None:
            phases = np.zeros(num_qubits)

        # Each qubit is |0> + e^{i phi} |1>, normalized
        # For product state, we can construct directly
        # Simple case: all qubits in |0> state
        psi = np.zeros(2 ** num_qubits, dtype=complex)
        psi[0] = 1.0  # |00...0>

        # Alternatively, generate random product states
        if np.any(phases != 0):
            # Construct product of single-qubit states
            psi = np.array([1.0], dtype=complex)
            for i in range(num_qubits):
                phi = phases[i]
                # |psi_i> = (|0> + e^{i phi} |1>) / sqrt(2)
                qubit_state = np.array([1, np.exp(1j * phi)], dtype=complex) / np.sqrt(2)
                psi = np.kron(psi, qubit_state)

        return QuantumState(psi, num_qubits=num_qubits, validate=True)

    @staticmethod
    def generate_ghz_state(num_qubits: int) -> 'QuantumState':
        """
        Generate a GHZ state: (|00...0> + |11...1>) / sqrt(2).

        Args:
            num_qubits: Number of qubits.

        Returns:
            GHZ state QuantumState.
        """
        dim = 2 ** num_qubits
        psi = np.zeros(dim, dtype=complex)
        psi[0] = 1.0 / np.sqrt(2)
        psi[dim - 1] = 1.0 / np.sqrt(2)

        return QuantumState(psi, num_qubits=num_qubits, validate=True)

    @staticmethod
    def generate_w_state(num_qubits: int) -> 'QuantumState':
        """
        Generate a W state: (|100...0> + |010...0> + ... + |00...01>) / sqrt(N).

        Args:
            num_qubits: Number of qubits.

        Returns:
            W state QuantumState.
        """
        dim = 2 ** num_qubits
        psi = np.zeros(dim, dtype=complex)

        # Set positions with single excitation
        for i in range(num_qubits):
            idx = 2 ** (num_qubits - 1 - i)  # Position of i-th qubit being |1>
            psi[idx] = 1.0 / np.sqrt(num_qubits)

        return QuantumState(psi, num_qubits=num_qubits, validate=True)

    @staticmethod
    def generate_bell_state(bell_type: str = 'phi_plus') -> 'QuantumState':
        """
        Generate one of the four Bell states.

        Args:
            bell_type: One of 'phi_plus', 'phi_minus', 'psi_plus', 'psi_minus'.

        Returns:
            2-qubit Bell state QuantumState.
        """
        bell_states = {
            'phi_plus': np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2),
            'phi_minus': np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2),
            'psi_plus': np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2),
            'psi_minus': np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2),
        }

        if bell_type not in bell_states:
            raise QuantumStateError(
                f"Unknown Bell state type: {bell_type}. "
                f"Choose from {list(bell_states.keys())}"
            )

        psi = bell_states[bell_type]
        return QuantumState(psi, num_qubits=2, validate=True)
