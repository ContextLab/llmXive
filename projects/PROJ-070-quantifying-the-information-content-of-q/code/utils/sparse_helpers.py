"""
Sparse matrix utility functions for quantum many-body simulations.

Provides CSR/CSC conversion, memory profiling, and helper functions
for working with sparse representations of quantum states and operators.
"""
import numpy as np
from scipy import sparse
from scipy.sparse import csr_matrix, csc_matrix, issparse
from typing import Union, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def convert_to_csr(matrix: Union[np.ndarray, sparse.spmatrix]) -> csr_matrix:
    """
    Convert a matrix or sparse matrix to CSR format.

    CSR (Compressed Sparse Row) is efficient for row slicing and matrix-vector products.

    Args:
        matrix: Input matrix (dense numpy array or sparse matrix)

    Returns:
        CSR sparse matrix

    Raises:
        ValueError: If input cannot be converted to sparse format
    """
    if issparse(matrix):
        if isinstance(matrix, csr_matrix):
            return matrix
        return matrix.tocsr()
    elif isinstance(matrix, np.ndarray):
        if matrix.ndim != 2:
            raise ValueError(f"Expected 2D array, got {matrix.ndim}D")
        return csr_matrix(matrix)
    else:
        raise ValueError(f"Unsupported input type: {type(matrix)}")


def convert_to_csc(matrix: Union[np.ndarray, sparse.spmatrix]) -> csc_matrix:
    """
    Convert a matrix or sparse matrix to CSC format.

    CSC (Compressed Sparse Column) is efficient for column slicing and certain
    linear algebra operations.

    Args:
        matrix: Input matrix (dense numpy array or sparse matrix)

    Returns:
        CSC sparse matrix

    Raises:
        ValueError: If input cannot be converted to sparse format
    """
    if issparse(matrix):
        if isinstance(matrix, csc_matrix):
            return matrix
        return matrix.tocsc()
    elif isinstance(matrix, np.ndarray):
        if matrix.ndim != 2:
            raise ValueError(f"Expected 2D array, got {matrix.ndim}D")
        return csc_matrix(matrix)
    else:
        raise ValueError(f"Unsupported input type: {type(matrix)}")


def get_memory_usage_bytes(matrix: Union[np.ndarray, sparse.spmatrix]) -> int:
    """
    Estimate memory usage of a matrix in bytes.

    For sparse matrices, this calculates the actual memory used by the
    compressed format (data + indices + indptr arrays).

    Args:
        matrix: Input matrix (dense or sparse)

    Returns:
        Estimated memory usage in bytes
    """
    if issparse(matrix):
        # Memory for sparse matrix: data array + row indices + column indices + indptr
        # CSR/CSC format: data (nnz * 8) + indices (nnz * 4) + indptr (n * 4)
        data_size = matrix.data.nbytes
        indices_size = matrix.indices.nbytes
        indptr_size = matrix.indptr.nbytes
        return data_size + indices_size + indptr_size
    elif isinstance(matrix, np.ndarray):
        return matrix.nbytes
    else:
        raise ValueError(f"Unsupported input type: {type(matrix)}")


def get_memory_usage_mb(matrix: Union[np.ndarray, sparse.spmatrix]) -> float:
    """
    Estimate memory usage of a matrix in megabytes.

    Args:
        matrix: Input matrix (dense or sparse)

    Returns:
        Estimated memory usage in MB
    """
    return get_memory_usage_bytes(matrix) / (1024 * 1024)


def get_sparsity(matrix: Union[np.ndarray, sparse.spmatrix]) -> float:
    """
    Calculate the sparsity of a matrix (fraction of zero elements).

    Args:
        matrix: Input matrix (dense or sparse)

    Returns:
        Sparsity value between 0.0 (dense) and 1.0 (all zeros)
    """
    if issparse(matrix):
        nnz = matrix.nnz  # number of stored (non-zero) elements
        total = matrix.shape[0] * matrix.shape[1]
        if total == 0:
            return 1.0
        return 1.0 - (nnz / total)
    elif isinstance(matrix, np.ndarray):
        total = matrix.size
        if total == 0:
            return 1.0
        nnz = np.count_nonzero(matrix)
        return 1.0 - (nnz / total)
    else:
        raise ValueError(f"Unsupported input type: {type(matrix)}")


def profile_sparse_matrix(matrix: Union[np.ndarray, sparse.spmatrix]) -> dict:
    """
    Generate a comprehensive profile of a sparse matrix's properties.

    Args:
        matrix: Input matrix (dense or sparse)

    Returns:
        Dictionary containing:
            - shape: tuple (rows, cols)
            - format: string representation of sparse format
            - nnz: number of non-zero elements
            - sparsity: fraction of zero elements
            - memory_bytes: estimated memory usage in bytes
            - memory_mb: estimated memory usage in MB
            - density: fraction of non-zero elements (1 - sparsity)
    """
    if not issparse(matrix):
        matrix = convert_to_csr(matrix)

    shape = matrix.shape
    nnz = matrix.nnz
    total = shape[0] * shape[1]
    sparsity = get_sparsity(matrix)
    density = 1.0 - sparsity
    memory_bytes = get_memory_usage_bytes(matrix)

    return {
        "shape": shape,
        "format": matrix.format,
        "nnz": nnz,
        "sparsity": sparsity,
        "density": density,
        "memory_bytes": memory_bytes,
        "memory_mb": memory_bytes / (1024 * 1024),
        "total_elements": total
    }


def ensure_sparse_format(
    matrix: Union[np.ndarray, sparse.spmatrix],
    target_format: str = "csr"
) -> sparse.spmatrix:
    """
    Ensure a matrix is in the specified sparse format.

    Args:
        matrix: Input matrix (dense or sparse)
        target_format: Target format ('csr', 'csc', 'coo', 'lil', 'dia')

    Returns:
        Sparse matrix in the target format

    Raises:
        ValueError: If target_format is not supported
    """
    format_map = {
        "csr": csr_matrix,
        "csc": csc_matrix,
        "coo": sparse.coo_matrix,
        "lil": sparse.lil_matrix,
        "dia": sparse.dia_matrix
    }

    if target_format not in format_map:
        raise ValueError(f"Unsupported format: {target_format}. "
                       f"Supported: {list(format_map.keys())}")

    if not issparse(matrix):
        matrix = sparse.csr_matrix(matrix)

    if matrix.format == target_format:
        return matrix

    return format_map[target_format](matrix)


def check_sparse_memory_efficiency(
    dense_matrix: np.ndarray,
    sparse_matrix: sparse.spmatrix,
    threshold_mb: float = 10.0
) -> Tuple[bool, float, float]:
    """
    Check if sparse representation is more memory-efficient than dense.

    Args:
        dense_matrix: Original dense matrix
        sparse_matrix: Sparse representation
        threshold_mb: Minimum memory savings (in MB) to consider sparse efficient

    Returns:
        Tuple of (is_efficient, dense_memory_mb, sparse_memory_mb)
    """
    dense_mem = get_memory_usage_mb(dense_matrix)
    sparse_mem = get_memory_usage_mb(sparse_matrix)
    savings = dense_mem - sparse_mem
    is_efficient = savings >= threshold_mb

    logger.debug(
        f"Memory efficiency check: dense={dense_mem:.2f}MB, "
        f"sparse={sparse_mem:.2f}MB, savings={savings:.2f}MB, "
        f"efficient={is_efficient}"
    )

    return is_efficient, dense_mem, sparse_mem