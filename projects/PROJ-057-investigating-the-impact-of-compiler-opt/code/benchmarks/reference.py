import os
import struct
import argparse
import logging
import numpy as np
from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import Tuple, Optional, Literal, Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set decimal precision to 512 bits (approx 154 decimal digits)
# As per Plan Note in tasks.md: "Task T006 resolves this to '512-bit'."
PRECISION_BITS = 512
# 512 bits / log2(10) ≈ 153.6 decimal digits
getcontext().prec = 154
getcontext().rounding = ROUND_HALF_UP

def decimal_matmul(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Perform Matrix Multiplication using high-precision Decimal arithmetic.
    
    Args:
        A: Input matrix (N, K)
        B: Input matrix (K, M)
        
    Returns:
        Result matrix (N, M) as float32 numpy array
    """
    if A.shape[1] != B.shape[0]:
        raise ValueError(f"Matrix dimensions mismatch: {A.shape} vs {B.shape}")
    
    n, k = A.shape
    m = B.shape[1]
    
    # Convert inputs to Decimal
    # We convert element-wise to preserve precision during the operation
    A_dec = [[Decimal(str(A[i, j])) for j in range(k)] for i in range(n)]
    B_dec = [[Decimal(str(B[i, j])) for j in range(m)] for i in range(k)]
    
    C_dec = [[Decimal(0) for _ in range(m)] for _ in range(n)]
    
    for i in range(n):
        for j in range(m):
            total = Decimal(0)
            for p in range(k):
                total += A_dec[i][p] * B_dec[p][j]
            C_dec[i][j] = total
    
    # Convert back to float32 numpy array
    C = np.zeros((n, m), dtype=np.float32)
    for i in range(n):
        for j in range(m):
            # Convert Decimal to float
            C[i, j] = float(C_dec[i][j])
            
    return C

def decimal_softmax(X: np.ndarray, axis: int = -1) -> np.ndarray:
    """
    Compute Softmax using high-precision Decimal arithmetic.
    
    Args:
        X: Input array
        axis: Axis along which to compute softmax
        
    Returns:
        Softmax result as float32 numpy array
    """
    # Shift for numerical stability (max subtraction)
    # We do this in float first to find the max, then convert to Decimal
    max_val = np.max(X, axis=axis, keepdims=True)
    X_shifted = X - max_val
    
    # Convert to Decimal
    shape = X.shape
    ndim = X.ndim
    
    # Flatten to 1D for easier processing if needed, but keep structure
    # We'll process element-wise
    X_dec = np.vectorize(lambda x: Decimal(str(x)))(X_shifted)
    
    # Compute exp using Decimal
    # Decimal doesn't have a native exp, so we use a Taylor series approximation
    # or convert to float for exp and back? 
    # For true high-precision, we need Decimal.exp() which exists in Python 3.3+
    # but we must ensure the context precision is respected.
    
    # Python's Decimal has an exp() method
    def safe_exp(d: Decimal) -> Decimal:
        try:
            return d.exp()
        except:
            # Fallback for very large numbers that might overflow even Decimal
            # This is rare with shifted input
            return Decimal(float(d).exp())
    
    exp_X = np.vectorize(safe_exp)(X_dec)
    
    # Sum along axis
    sum_exp = np.sum(exp_X, axis=axis, keepdims=True)
    
    # Compute softmax
    softmax_X = exp_X / sum_exp
    
    # Convert back to float32
    return np.vectorize(lambda x: float(x))(softmax_X).astype(np.float32)

def decimal_layernorm(X: np.ndarray, gamma: np.ndarray, beta: np.ndarray, epsilon: float = 1e-5) -> np.ndarray:
    """
    Compute Layer Normalization using high-precision Decimal arithmetic.
    
    Args:
        X: Input array (N, D)
        gamma: Scale parameter (D,)
        beta: Shift parameter (D,)
        epsilon: Small constant for numerical stability
        
    Returns:
        Normalized output as float32 numpy array
    """
    if X.shape[-1] != gamma.shape[0] or X.shape[-1] != beta.shape[0]:
        raise ValueError(f"Dimension mismatch: X last dim {X.shape[-1]} vs gamma/beta {gamma.shape[0]}")
    
    # Convert inputs to Decimal
    # We need to handle the mean and variance calculation in high precision
    
    # Convert X to Decimal
    X_dec = np.vectorize(lambda x: Decimal(str(x)))(X)
    gamma_dec = np.vectorize(lambda x: Decimal(str(x)))(gamma)
    beta_dec = np.vectorize(lambda x: Decimal(str(x)))(beta)
    epsilon_dec = Decimal(str(epsilon))
    
    # Compute mean along last axis
    mean = np.mean(X_dec, axis=-1, keepdims=True)
    
    # Compute variance
    var = np.mean((X_dec - mean) ** 2, axis=-1, keepdims=True)
    
    # Compute standard deviation
    std = np.sqrt(var + epsilon_dec)
    
    # Normalize
    X_norm = (X_dec - mean) / std
    
    # Scale and shift
    # Broadcast gamma and beta to match X shape
    # gamma and beta are 1D (D,), X_norm is (N, D)
    # We need to broadcast correctly
    output_dec = X_norm * gamma_dec + beta_dec
    
    # Convert back to float32
    return np.vectorize(lambda x: float(x))(output_dec).astype(np.float32)

def generate_reference_tensor(tensor_path: str, kernel_type: str) -> np.ndarray:
    """
    Load a tensor from binary file and compute the reference result.
    
    Args:
        tensor_path: Path to the binary tensor file
        kernel_type: Type of kernel ('matmul', 'softmax', 'layernorm')
        
    Returns:
        Reference result as float32 numpy array
    """
    # Load binary tensor
    # Assuming the format: header (dims) + data (float32)
    with open(tensor_path, 'rb') as f:
        # Read header: 3 integers (N, K, M or N, D)
        header_size = 3 * 4  # 3 integers
        header_data = f.read(header_size)
        dims = struct.unpack('iii', header_data)
        
        if kernel_type == 'matmul':
            n, k, m = dims
            # Read A and B
            # A is N x K, B is K x M
            # Assuming concatenated: A then B
            a_size = n * k * 4
            b_size = k * m * 4
            
            A_data = f.read(a_size)
            B_data = f.read(b_size)
            
            A = np.frombuffer(A_data, dtype=np.float32).reshape(n, k)
            B = np.frombuffer(B_data, dtype=np.float32).reshape(k, m)
            
            result = decimal_matmul(A, B)
            
        elif kernel_type == 'softmax':
            n, d, _ = dims
            data = np.frombuffer(f.read(), dtype=np.float32).reshape(n, d)
            result = decimal_softmax(data)
            
        elif kernel_type == 'layernorm':
            n, d, _ = dims
            # Read X, gamma, beta
            x_size = n * d * 4
            gamma_size = d * 4
            beta_size = d * 4
            
            X_data = f.read(x_size)
            gamma_data = f.read(gamma_size)
            beta_data = f.read(beta_size)
            
            X = np.frombuffer(X_data, dtype=np.float32).reshape(n, d)
            gamma = np.frombuffer(gamma_data, dtype=np.float32).reshape(d)
            beta = np.frombuffer(beta_data, dtype=np.float32).reshape(d)
            
            result = decimal_layernorm(X, gamma, beta)
        else:
            raise ValueError(f"Unknown kernel type: {kernel_type}")
    
    return result

def save_tensor_to_binary(tensor: np.ndarray, output_path: str, kernel_type: str):
    """
    Save a tensor to binary file.
    
    Args:
        tensor: Tensor to save
        output_path: Output file path
        kernel_type: Type of kernel for header info
    """
    with open(output_path, 'wb') as f:
        if kernel_type == 'matmul':
            # For matmul result, we save the output dimensions
            n, m = tensor.shape
            # Header: N, K, M (K is not in result but needed for context? No, just result dims)
            # Actually, for reference output, we just need the result dims
            # But to be consistent with input format, let's save N, 1, M or just N, M?
            # Let's use N, M, 1 for consistency with 3-int header
            header = struct.pack('iii', n, m, 1)
            f.write(header)
            f.write(tensor.tobytes())
            
        elif kernel_type == 'softmax':
            n, d = tensor.shape
            header = struct.pack('iii', n, d, 1)
            f.write(header)
            f.write(tensor.tobytes())
            
        elif kernel_type == 'layernorm':
            n, d = tensor.shape
            header = struct.pack('iii', n, d, 1)
            f.write(header)
            f.write(tensor.tobytes())

def run_reference_benchmarks(input_dir: str, output_dir: str, config_list: List[Dict[str, Any]]):
    """
    Run reference benchmarks for a list of configurations.
    
    Args:
        input_dir: Directory containing input binary tensors
        output_dir: Directory to save reference results
        config_list: List of configuration dicts with keys:
            - 'config_id': Unique identifier
            - 'kernel_type': 'matmul', 'softmax', or 'layernorm'
            - 'tensor_file': Filename of input tensor
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for config in config_list:
        config_id = config['config_id']
        kernel_type = config['kernel_type']
        tensor_file = config['tensor_file']
        
        input_file = input_path / tensor_file
        
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            continue
        
        logger.info(f"Processing {config_id}: {kernel_type} from {tensor_file}")
        
        try:
            result = generate_reference_tensor(str(input_file), kernel_type)
            
            output_file = output_path / f"{config_id}_reference.bin"
            save_tensor_to_binary(result, str(output_file), kernel_type)
            
            logger.info(f"Saved reference result to {output_file}")
            
        except Exception as e:
            logger.error(f"Error processing {config_id}: {e}")
            raise

def main():
    """Main entry point for running reference benchmarks."""
    parser = argparse.ArgumentParser(description='High-precision reference engine')
    parser.add_argument('--input-dir', type=str, default='data/raw',
                      help='Directory containing input binary tensors')
    parser.add_argument('--output-dir', type=str, default='data/raw',
                      help='Directory to save reference results')
    parser.add_argument('--config-file', type=str, required=True,
                      help='JSON file containing list of configurations to process')
    
    args = parser.parse_args()
    
    # Load configurations
    with open(args.config_file, 'r') as f:
        config_list = json.load(f)
    
    run_reference_benchmarks(args.input_dir, args.output_dir, config_list)

if __name__ == '__main__':
    main()
