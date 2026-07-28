import numpy as np
from scipy.sparse.linalg import svds
from scipy.sparse import csr_matrix
import gzip
import lzma
import bz2
from logging_config import logger

def check_numerical_stability(data: np.ndarray) -> bool:
    """Check for NaN or Inf values in data."""
    if np.any(np.isnan(data)) or np.any(np.isinf(data)):
        logger.error("Numerical instability detected: NaN or Inf found in data.")
        return False
    return True

def calculate_entanglement_entropy(psi: np.ndarray, partition: tuple) -> float:
    """
    Calculate bipartite entanglement entropy using sparse SVD.
    psi: 1D array of wavefunction coefficients.
    partition: (size_A, size_B) tuple indicating subsystem dimensions.
    """
    if not check_numerical_stability(psi):
        raise E_DATA_INSUFFICIENT("Wavefunction contains NaN/Inf.")
    
    # Reshape into matrix for Schmidt decomposition
    # psi is size 2^N. Partition sizes should multiply to 2^N.
    size_A, size_B = partition
    matrix = psi.reshape(size_A, size_B)
    
    # Convert to sparse CSR for svds
    sparse_mat = csr_matrix(matrix)
    
    # Compute singular values (k = min(size_A, size_B) - 1 to avoid full decomposition overhead if large)
    # For entanglement, we need all non-zero singular values, but svds is approximate.
    # For small systems (N<=20), full SVD might be safer, but we adhere to sparse requirement.
    k = min(size_A, size_B) - 1
    if k <= 0: k = 1
    
    try:
        u, s, vt = svds(sparse_mat, k=k)
    except Exception as e:
        logger.warning(f"svds failed, falling back to dense SVD for small matrix: {e}")
        # Fallback for very small matrices where sparse overhead/bugs might occur
        u, s, vt = np.linalg.svd(matrix, full_matrices=False)
    
    # Squared singular values are eigenvalues of reduced density matrix
    # Entanglement entropy: - sum(lambda_i * log(lambda_i))
    # Handle zero eigenvalues to avoid log(0)
    s_squared = s ** 2
    s_squared = s_squared[s_squared > 1e-14]
    
    if len(s_squared) == 0:
        return 0.0
    
    entropy = -np.sum(s_squared * np.log(s_squared))
    return float(entropy)

def quantize_wavefunction(psi: np.ndarray, bits: int = 16) -> bytes:
    """
    Quantize raw wavefunction coefficients to fixed-point signed integers (16-bit).
    Returns the byte representation of the quantized array.
    """
    # Normalize to [-1, 1] range for quantization
    max_val = np.max(np.abs(psi))
    if max_val == 0:
        max_val = 1.0
    
    # Scale and convert to int16
    # int16 range: -32768 to 32767
    scale_factor = 32767.0 / max_val
    real_quant = np.floor(np.real(psi) * scale_factor).astype(np.int16)
    imag_quant = np.floor(np.imag(psi) * scale_factor).astype(np.int16)
    
    # Pack into bytes
    return real_quant.tobytes() + imag_quant.tobytes()

def calculate_ncd(psi: np.ndarray, baseline_psi: np.ndarray) -> float:
    """
    Calculate Normalized Compression Distance (NCD) between two wavefunctions.
    Uses gzip as the compressor.
    """
    # Quantize both
    data_a = quantize_wavefunction(psi)
    data_b = quantize_wavefunction(baseline_psi)
    data_ab = data_a + data_b
    
    # Compressors
    def compress(data):
        return len(gzip.compress(data))
    
    len_a = compress(data_a)
    len_b = compress(data_b)
    len_ab = compress(data_ab)
    
    # NCD = (C(AB) - min(C(A), C(B))) / max(C(A), C(B))
    numerator = len_ab - min(len_a, len_b)
    denominator = max(len_a, len_b)
    
    if denominator == 0:
        return 0.0
    
    return float(numerator / denominator)
