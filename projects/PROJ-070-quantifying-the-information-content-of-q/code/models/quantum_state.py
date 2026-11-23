"""
QuantumState entity class supporting sparse representation for many-body quantum systems.

This module defines the core data structure for representing quantum states in the
llmXive pipeline. It supports both dense numpy arrays and sparse scipy matrices,
with automatic conversion and validation capabilities.

Key features:
- Support for sparse (CSR/CSC) and dense representations
- Automatic normalization and validation
- Integration with logging infrastructure for numerical stability checks
- Compatibility with HDF5 serialization via data_loader
"""

import numpy as np
from scipy import sparse
from typing import Optional, Union, Tuple, Dict, Any
from logging_config import logger


class QuantumStateError(Exception):
    """Custom exception for QuantumState related errors."""
    pass


class QuantumState:
    """
    Represents a quantum state in a many-body system.

    This class supports both dense and sparse representations of quantum states,
    automatically handling conversions and maintaining numerical stability.

    Attributes:
        data (Union[np.ndarray, sparse.csr_matrix]): The state vector or density matrix.
        system_size (int): Number of qubits/spins in the system.
        subsystem_split (Optional[Tuple[int, int]]): Split point for bipartite analysis.
        is_normalized (bool): Whether the state is normalized.
        representation_type (str): 'dense' or 'sparse'.
        metadata (Dict[str, Any]): Additional state information.
    """

    def __init__(
        self,
        data: Union[np.ndarray, sparse.csr_matrix, sparse.csc_matrix],
        system_size: Optional[int] = None,
        subsystem_split: Optional[Tuple[int, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a QuantumState instance.

        Args:
            data: State vector (1D) or density matrix (2D). Can be dense numpy array
                 or sparse matrix (CSR/CSC format).
            system_size: Number of qubits/spins. If None, inferred from data shape.
            subsystem_split: Tuple (A_size, B_size) for bipartite systems.
            metadata: Optional dictionary for additional state information.

        Raises:
            QuantumStateError: If data is invalid or inconsistent with system_size.
        """
        self.metadata = metadata or {}
        self._validate_input(data)

        # Convert to appropriate sparse format if needed
        if sparse.issparse(data):
            # Ensure CSR format for efficient operations
            if not isinstance(data, (sparse.csr_matrix, sparse.csc_matrix)):
                data = data.tocsr()
            self.data = data
            self.representation_type = 'sparse'
        else:
            self.data = np.asarray(data, dtype=np.complex128)
            self.representation_type = 'dense'

        # Infer or validate system size
        if system_size is None:
            system_size = self._infer_system_size()
        self.system_size = system_size

        # Set subsystem split if provided
        if subsystem_split is not None:
            if len(subsystem_split) != 2:
                raise QuantumStateError("subsystem_split must be a tuple of two integers")
            if sum(subsystem_split) != system_size:
                raise QuantumStateError(
                    f"subsystem_split {subsystem_split} does not sum to system_size {system_size}"
                )
        self.subsystem_split = subsystem_split

        # Validate and normalize
        self._check_numerical_stability()
        self.is_normalized = self._normalize_if_needed()

    def _validate_input(self, data: Any) -> None:
        """Validate the input data format and content."""
        if data is None:
            raise QuantumStateError("Data cannot be None")

        if sparse.issparse(data):
            if not isinstance(data, (sparse.csr_matrix, sparse.csc_matrix, sparse.coo_matrix)):
                raise QuantumStateError(
                    f"Sparse data must be CSR, CSC, or COO format, got {type(data)}"
                )
            if data.ndim not in (1, 2):
                raise QuantumStateError(f"Sparse data must be 1D or 2D, got {data.ndim}D")
        else:
            try:
                arr = np.asarray(data)
            except (ValueError, TypeError) as e:
                raise QuantumStateError(f"Cannot convert data to numpy array: {e}")

            if arr.ndim not in (1, 2):
                raise QuantumStateError(f"Dense data must be 1D or 2D, got {arr.ndim}D")

            if not np.issubdtype(arr.dtype, np.complexfloating):
                logger.warning(
                    f"Data dtype {arr.dtype} is not complex, converting to complex128"
                )

    def _infer_system_size(self) -> int:
        """Infer system size (number of qubits) from data shape."""
        dim = self.data.shape[0] if self.data.ndim == 1 else self.data.shape[0]

        # For state vectors: dim = 2^N
        if self.data.ndim == 1 or (self.data.ndim == 2 and self.data.shape[0] == self.data.shape[1]):
            # Check if dimension is a power of 2
            if dim <= 0:
                raise QuantumStateError(f"Invalid dimension {dim}")

            # Calculate N such that 2^N = dim
            n = np.log2(dim)
            if not np.isclose(n, round(n)):
                # For density matrices, dim = (2^N)^2 = 4^N
                n = np.log2(dim) / 2
                if not np.isclose(n, round(n)):
                    raise QuantumStateError(
                        f"Dimension {dim} is not a valid power of 2 for state vector or density matrix"
                    )

            return int(round(n))

        # For rectangular matrices (e.g., reshaped for SVD)
        if self.data.ndim == 2 and self.data.shape[0] != self.data.shape[1]:
            # This might be a reshaped state for bipartite analysis
            # We'll store the total dimension and let subsystem_split clarify
            total_dim = self.data.shape[0] * self.data.shape[1]
            n = np.log2(total_dim)
            if np.isclose(n, round(n)):
                return int(round(n))

        raise QuantumStateError(f"Cannot infer system size from shape {self.data.shape}")

    def _check_numerical_stability(self) -> None:
        """Check for NaN or Inf values in the data."""
        if sparse.issparse(self.data):
            # For sparse matrices, check the data attribute
            if hasattr(self.data, 'data'):
                if np.any(np.isnan(self.data.data)) or np.any(np.isinf(self.data.data)):
                    logger.error("Numerical instability detected: NaN or Inf in sparse data")
                    raise QuantumStateError("Numerical instability: NaN or Inf in state data")
        else:
            if np.any(np.isnan(self.data)) or np.any(np.isinf(self.data)):
                logger.error("Numerical instability detected: NaN or Inf in dense data")
                raise QuantumStateError("Numerical instability: NaN or Inf in state data")

    def _normalize_if_needed(self) -> bool:
        """Normalize the state if it's not already normalized."""
        norm = self.compute_norm()

        if np.isclose(norm, 1.0, atol=1e-10):
            return True

        if norm == 0:
            raise QuantumStateError("Cannot normalize zero vector")

        # Log the normalization
        logger.debug(f"Normalizing state from norm {norm:.6f} to 1.0")

        if sparse.issparse(self.data):
            self.data = self.data / norm
        else:
            self.data = self.data / norm

        return True

    def compute_norm(self) -> float:
        """Compute the L2 norm of the state vector."""
        if sparse.issparse(self.data):
            # For sparse matrices, compute norm efficiently
            return np.sqrt(np.abs(self.data).multiply(self.data).sum())
        else:
            return np.linalg.norm(self.data)

    def get_reduced_density_matrix(self, subsystem_A: int) -> Union[np.ndarray, sparse.csr_matrix]:
        """
        Compute the reduced density matrix for subsystem A.

        Args:
            subsystem_A: Size of subsystem A (number of qubits).

        Returns:
            Reduced density matrix for subsystem A.

        Raises:
            QuantumStateError: If state is not a pure state vector or subsystem size is invalid.
        """
        if self.data.ndim != 1:
            raise QuantumStateError("Reduced density matrix computation requires a pure state vector")

        N = self.system_size
        n_A = subsystem_A
        n_B = N - n_A

        if n_A <= 0 or n_B <= 0:
            raise QuantumStateError(f"Invalid subsystem sizes: A={n_A}, B={n_B}")

        dim_A = 2 ** n_A
        dim_B = 2 ** n_B

        # Reshape state vector into a matrix for SVD
        # |ψ⟩ = Σᵢⱼ ψᵢⱼ |i⟩_A ⊗ |j⟩_B
        psi_matrix = self.data.reshape(dim_A, dim_B)

        # Compute reduced density matrix: ρ_A = Tr_B(|ψ⟩⟨ψ|) = ψ_matrix @ ψ_matrix†
        if sparse.issparse(psi_matrix):
            # For sparse: ρ_A = psi_matrix @ psi_matrix.conj().T
            rho_A = psi_matrix.dot(psi_matrix.conj().T).tocsr()
        else:
            rho_A = psi_matrix @ psi_matrix.conj().T

        return rho_A

    def to_dense(self) -> np.ndarray:
        """Convert sparse representation to dense numpy array."""
        if self.representation_type == 'dense':
            return self.data.copy()
        return self.data.toarray()

    def to_sparse(self, format: str = 'csr') -> sparse.spmatrix:
        """
        Convert dense representation to sparse matrix.

        Args:
            format: Target sparse format ('csr', 'csc', 'coo', etc.)

        Returns:
            Sparse matrix in the specified format.
        """
        if self.representation_type == 'sparse':
            if isinstance(self.data, getattr(sparse, f'{format}_matrix')):
                return self.data
            return self.data.asformat(format)

        return sparse.csr_matrix(self.data).asformat(format)

    def get_fidelity(self, other: 'QuantumState') -> float:
        """
        Compute fidelity between this state and another.

        For pure states: F = |⟨ψ|φ⟩|²

        Args:
            other: Another QuantumState instance.

        Returns:
            Fidelity value between 0 and 1.
        """
        if not isinstance(other, QuantumState):
            raise QuantumStateError("Fidelity computation requires another QuantumState")

        if self.system_size != other.system_size:
            raise QuantumStateError(
                f"System size mismatch: {self.system_size} vs {other.system_size}"
            )

        # Ensure both are in compatible formats
        if self.representation_type != other.representation_type:
            # Convert to dense for comparison
            vec1 = self.to_dense()
            vec2 = other.to_dense()
        else:
            vec1 = self.data
            vec2 = other.data

        # Compute inner product
        if sparse.issparse(vec1):
            overlap = np.abs(vec1.conj().dot(vec2))
        else:
            overlap = np.abs(np.vdot(vec1, vec2))

        return float(overlap ** 2)

    def get_entropy_per_spin(self, subsystem_A: int) -> float:
        """
        Compute entanglement entropy per spin for a bipartition.

        Args:
            subsystem_A: Size of subsystem A.

        Returns:
            Entanglement entropy divided by subsystem size.
        """
        from metrics import calculate_entanglement_entropy

        rho_A = self.get_reduced_density_matrix(subsystem_A)
        total_entropy = calculate_entanglement_entropy(rho_A)

        return total_entropy / subsystem_A

    def __repr__(self) -> str:
        return (
            f"QuantumState(system_size={self.system_size}, "
            f"representation={self.representation_type}, "
            f"normalized={self.is_normalized})"
        )

    def __str__(self) -> str:
        return (
            f"QuantumState:\n"
            f"  System size: {self.system_size} qubits\n"
            f"  Representation: {self.representation_type}\n"
            f"  Dimension: {self.data.shape}\n"
            f"  Normalized: {self.is_normalized}\n"
            f"  Subsystem split: {self.subsystem_split}"
        )

    def validate(self) -> Tuple[bool, str]:
        """
        Validate the quantum state for downstream processing.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            # Check dimensions
            dim = self.data.shape[0] if self.data.ndim == 1 else self.data.shape[0]
            expected_dim = 2 ** self.system_size

            if self.data.ndim == 1:
                if dim != expected_dim:
                    return False, f"Dimension mismatch: {dim} != {expected_dim}"
            elif self.data.ndim == 2:
                if dim != expected_dim or self.data.shape[1] != expected_dim:
                    return False, f"Density matrix dimension mismatch"

            # Check normalization
            if not np.isclose(self.compute_norm(), 1.0, atol=1e-6):
                return False, f"State not normalized: norm = {self.compute_norm()}"

            # Check for numerical issues
            if sparse.issparse(self.data):
                if np.any(np.isnan(self.data.data)) or np.any(np.isinf(self.data.data)):
                    return False, "Numerical instability: NaN or Inf detected"
            else:
                if np.any(np.isnan(self.data)) or np.any(np.isinf(self.data)):
                    return False, "Numerical instability: NaN or Inf detected"

            return True, "Valid"

        except Exception as e:
            return False, f"Validation failed: {str(e)}"

    @classmethod
    def from_hdf5(cls, filepath: str) -> 'QuantumState':
        """
        Load a QuantumState from an HDF5 file.

        Args:
            filepath: Path to the HDF5 file.

        Returns:
            QuantumState instance.

        Raises:
            QuantumStateError: If file is invalid or cannot be read.
        """
        import h5py

        try:
            with h5py.File(filepath, 'r') as f:
                # Check for required datasets
                if 'data' not in f:
                    raise QuantumStateError("HDF5 file missing 'data' dataset")

                if 'system_size' not in f.attrs:
                    raise QuantumStateError("HDF5 file missing 'system_size' attribute")

                # Load data
                data = f['data'][...]

                # Check if sparse
                is_sparse = f.attrs.get('is_sparse', False)
                if is_sparse:
                    if 'indices' not in f or 'indptr' not in f:
                        raise QuantumStateError("Sparse data missing indices/indptr")

                    data = sparse.csr_matrix(
                        (data, f['indices'][...], f['indptr'][...]),
                        shape=f['data'].shape
                    )

                system_size = int(f.attrs['system_size'])
                subsystem_split = None
                if 'subsystem_split' in f.attrs:
                    split_str = f.attrs['subsystem_split']
                    if isinstance(split_str, bytes):
                        split_str = split_str.decode('utf-8')
                    subsystem_split = tuple(map(int, split_str.split(',')))

                metadata = {}
                if 'metadata' in f.attrs:
                    meta_str = f.attrs['metadata']
                    if isinstance(meta_str, bytes):
                        meta_str = meta_str.decode('utf-8')
                    # Simple JSON-like parsing for metadata
                    try:
                        import json
                        metadata = json.loads(meta_str)
                    except:
                        metadata = {'raw': meta_str}

                return cls(
                    data=data,
                    system_size=system_size,
                    subsystem_split=subsystem_split,
                    metadata=metadata
                )

        except Exception as e:
            raise QuantumStateError(f"Failed to load QuantumState from HDF5: {e}")

    def to_hdf5(self, filepath: str) -> None:
        """
        Save the QuantumState to an HDF5 file.

        Args:
            filepath: Path to save the HDF5 file.
        """
        import h5py
        import json

        with h5py.File(filepath, 'w') as f:
            # Store data
            if sparse.issparse(self.data):
                f.create_dataset('data', data=self.data.data)
                f.create_dataset('indices', data=self.data.indices)
                f.create_dataset('indptr', data=self.data.indptr)
                f.attrs['is_sparse'] = True
                f['data'].shape = self.data.shape
            else:
                f.create_dataset('data', data=self.data)
                f.attrs['is_sparse'] = False

            # Store attributes
            f.attrs['system_size'] = self.system_size
            if self.subsystem_split:
                split_str = ','.join(map(str, self.subsystem_split))
                f.attrs['subsystem_split'] = split_str

            if self.metadata:
                meta_str = json.dumps(self.metadata)
                f.attrs['metadata'] = meta_str

            f.attrs['representation_type'] = self.representation_type
            f.attrs['is_normalized'] = self.is_normalized