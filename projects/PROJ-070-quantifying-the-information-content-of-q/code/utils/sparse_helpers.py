"""
Sparse matrix utility functions for quantum many-body simulations.

Provides CSR/CSC conversion, memory profiling, and sparsity analysis tools
optimized for large sparse matrices encountered in entanglement calculations.
"""
import numpy as np
from scipy import sparse
from scipy.sparse import csr_matrix, csc_matrix, issparse
from typing import Union, Tuple, Optional, Dict, Any
import logging
import sys
import resource
import gc

# Configure logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def convert_to_csr(matrix: Union[np.ndarray, sparse.spmatrix]) -> csr_matrix:
    """
    Convert a matrix to CSR (Compressed Sparse Row) format.
    
    CSR is efficient for row slicing and matrix-vector products.
    
    Args:
        matrix: Input array or sparse matrix.
    
    Returns:
        CSR sparse matrix.
    
    Raises:
        TypeError: If input cannot be converted to sparse matrix.
    """
    if issparse(matrix):
        if isinstance(matrix, csr_matrix):
            return matrix
        return matrix.tocsr()
    elif isinstance(matrix, np.ndarray):
        return csr_matrix(matrix)
    else:
        raise TypeError(f"Cannot convert {type(matrix)} to sparse matrix")

def convert_to_csc(matrix: Union[np.ndarray, sparse.spmatrix]) -> csc_matrix:
    """
    Convert a matrix to CSC (Compressed Sparse Column) format.
    
    CSC is efficient for column slicing and column-wise operations.
    
    Args:
        matrix: Input array or sparse matrix.
    
    Returns:
        CSC sparse matrix.
    
    Raises:
        TypeError: If input cannot be converted to sparse matrix.
    """
    if issparse(matrix):
        if isinstance(matrix, csc_matrix):
            return matrix
        return matrix.tocsc()
    elif isinstance(matrix, np.ndarray):
        return csc_matrix(matrix)
    else:
        raise TypeError(f"Cannot convert {type(matrix)} to sparse matrix")

def get_memory_usage_bytes() -> int:
    """
    Get current memory usage of the process in bytes.
    
    Returns:
        Memory usage in bytes.
    
    Note:
        Uses resource module (Unix) or returns 0 on Windows.
    """
    try:
        # Works on Unix/Linux/macOS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS, bytes on some systems
        # On Linux: ru_maxrss is in KB
        maxrss_kb = usage.ru_maxrss
        return maxrss_kb * 1024
    except Exception as e:
        logger.warning(f"Could not get memory usage: {e}")
        return 0

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in megabytes.
    
    Returns:
        Memory usage in MB.
    """
    return get_memory_usage_bytes() / (1024 * 1024)

def get_sparsity(matrix: sparse.spmatrix) -> float:
    """
    Calculate the sparsity of a sparse matrix.
    
    Sparsity is defined as the fraction of zero elements.
    
    Args:
        matrix: Input sparse matrix.
    
    Returns:
        Sparsity value between 0.0 (dense) and 1.0 (all zeros).
    """
    if not issparse(matrix):
        matrix = sparse.csr_matrix(matrix)
    
    total_elements = matrix.shape[0] * matrix.shape[1]
    if total_elements == 0:
        return 1.0
    
    nnz = matrix.nnz
    sparsity = 1.0 - (nnz / total_elements)
    return sparsity

def profile_sparse_matrix(
    matrix: sparse.spmatrix,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Profile a sparse matrix with detailed statistics.
    
    Args:
        matrix: Input sparse matrix.
        name: Optional name for the matrix in the report.
    
    Returns:
        Dictionary containing:
            - name: Matrix identifier
            - shape: (rows, cols)
            - nnz: Number of non-zero elements
            - sparsity: Fraction of zeros
            - memory_bytes: Approximate memory usage of sparse structure
            - format: Sparse format string
            - dtype: Data type
    """
    if not issparse(matrix):
        matrix = sparse.csr_matrix(matrix)
    
    shape = matrix.shape
    nnz = matrix.nnz
    total_elements = shape[0] * shape[1]
    sparsity = 1.0 - (nnz / total_elements) if total_elements > 0 else 1.0
    
    # Approximate memory usage for CSR/CSC:
    # data (nnz) + indices (nnz) + indptr (n+1)
    # Each is typically 8 bytes (float64) or 4 bytes (int32/int64)
    data_size = matrix.data.nbytes
    indices_size = matrix.indices.nbytes
    indptr_size = matrix.indptr.nbytes
    memory_bytes = data_size + indices_size + indptr_size
    
    profile = {
        'name': name or 'unnamed',
        'shape': shape,
        'nnz': nnz,
        'sparsity': sparsity,
        'memory_bytes': memory_bytes,
        'memory_mb': memory_bytes / (1024 * 1024),
        'format': matrix.format,
        'dtype': str(matrix.dtype)
    }
    
    logger.info(f"Profiled matrix '{profile['name']}': "
               f"shape={shape}, nnz={nnz}, sparsity={sparsity:.4f}, "
               f"mem={profile['memory_mb']:.2f} MB")
    
    return profile

def ensure_sparse_format(
    matrix: Union[np.ndarray, sparse.spmatrix],
    target_format: str = 'csr',
    dtype: Optional[np.dtype] = None
) -> sparse.spmatrix:
    """
    Ensure matrix is in the specified sparse format.
    
    Args:
        matrix: Input array or sparse matrix.
        target_format: Target format ('csr', 'csc', 'coo', 'lil', etc.).
        dtype: Optional data type to cast to.
    
    Returns:
        Sparse matrix in target format.
    
    Raises:
        ValueError: If target_format is not a valid sparse format.
    """
    valid_formats = {'csr', 'csc', 'coo', 'lil', 'dok', 'bsr', 'dia'}
    if target_format not in valid_formats:
        raise ValueError(f"Invalid format '{target_format}'. "
                       f"Valid formats: {valid_formats}")
    
    if not issparse(matrix):
        matrix = sparse.csr_matrix(matrix)
    
    # Convert to target format
    if target_format == 'csr':
        result = matrix.tocsr()
    elif target_format == 'csc':
        result = matrix.tocsc()
    elif target_format == 'coo':
        result = matrix.tocoo()
    elif target_format == 'lil':
        result = matrix.tolil()
    elif target_format == 'dok':
        result = matrix.todok()
    elif target_format == 'bsr':
        result = matrix.tobsr()
    elif target_format == 'dia':
        result = matrix.todia()
    else:
        result = matrix  # fallback
    
    if dtype is not None:
        result = result.astype(dtype)
    
    return result

def check_sparse_memory_efficiency(
    dense_matrix: np.ndarray,
    sparse_matrix: sparse.spmatrix,
    threshold_mb: float = 100.0
) -> Tuple[bool, Dict[str, float]]:
    """
    Check if sparse representation is more memory-efficient than dense.
    
    Args:
        dense_matrix: Original dense array.
        sparse_matrix: Sparse representation.
        threshold_mb: Minimum memory savings (in MB) to consider it efficient.
    
    Returns:
        Tuple of (is_efficient, stats_dict):
            - is_efficient: True if sparse saves >= threshold_mb
            - stats_dict: Contains dense_mb, sparse_mb, savings_mb, sparsity
    """
    dense_bytes = dense_matrix.nbytes
    dense_mb = dense_bytes / (1024 * 1024)
    
    sparse_profile = profile_sparse_matrix(sparse_matrix)
    sparse_mb = sparse_profile['memory_mb']
    
    savings_mb = dense_mb - sparse_mb
    sparsity = sparse_profile['sparsity']
    
    stats = {
        'dense_mb': dense_mb,
        'sparse_mb': sparse_mb,
        'savings_mb': savings_mb,
        'sparsity': sparsity
    }
    
    is_efficient = savings_mb >= threshold_mb
    
    logger.info(f"Memory efficiency check: dense={dense_mb:.2f} MB, "
               f"sparse={sparse_mb:.2f} MB, savings={savings_mb:.2f} MB, "
               f"sparsity={sparsity:.4f}, efficient={is_efficient}")
    
    return is_efficient, stats

def estimate_svd_memory(
    matrix: sparse.spmatrix,
    k: int,
    dtype_size_bytes: int = 8
) -> Dict[str, float]:
    """
    Estimate memory requirements for sparse SVD computation.
    
    Args:
        matrix: Input sparse matrix.
        k: Number of singular vectors to compute.
        dtype_size_bytes: Size of data type in bytes (default 8 for float64).
    
    Returns:
        Dictionary with memory estimates:
            - matrix_mb: Memory for sparse matrix
            - u_vectors_mb: Memory for left singular vectors
            - vt_vectors_mb: Memory for right singular vectors
            - s_vector_mb: Memory for singular values
            - total_estimated_mb: Total estimated memory
    """
    if not issparse(matrix):
        matrix = sparse.csr_matrix(matrix)
    
    profile = profile_sparse_matrix(matrix)
    matrix_mb = profile['memory_mb']
    
    m, n = matrix.shape
    
    # U: m x k
    u_vectors_mb = (m * k * dtype_size_bytes) / (1024 * 1024)
    # Vt: k x n
    vt_vectors_mb = (k * n * dtype_size_bytes) / (1024 * 1024)
    # S: k
    s_vector_mb = (k * dtype_size_bytes) / (1024 * 1024)
    
    total_estimated_mb = matrix_mb + u_vectors_mb + vt_vectors_mb + s_vector_mb
    
    logger.debug(f"SVD memory estimate: k={k}, "
                f"matrix={matrix_mb:.2f} MB, "
                f"U={u_vectors_mb:.2f} MB, "
                f"Vt={vt_vectors_mb:.2f} MB, "
                f"S={s_vector_mb:.2f} MB, "
                f"total={total_estimated_mb:.2f} MB")
    
    return {
        'matrix_mb': matrix_mb,
        'u_vectors_mb': u_vectors_mb,
        'vt_vectors_mb': vt_vectors_mb,
        's_vector_mb': s_vector_mb,
        'total_estimated_mb': total_estimated_mb
    }

def reduce_memory_by_gc() -> float:
    """
    Force garbage collection and return memory freed.
    
    Returns:
        Memory freed in MB (approximate).
    """
    before = get_memory_usage_mb()
    gc.collect()
    after = get_memory_usage_mb()
    freed = before - after
    if freed > 0:
        logger.info(f"Garbage collection freed {freed:.2f} MB")
    return freed