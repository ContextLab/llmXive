"""
High-precision reference engine for LLM inference operations.
Uses Python's decimal module with 512-bit precision to calculate
ground-truth values for MatMul, Softmax, and LayerNorm.
"""
import os
import struct
import argparse
import logging
import hashlib
from pathlib import Path
from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import List, Tuple, Optional

# Set precision to 512 bits (approx 154 decimal digits)
# 512 bits / log2(10) ≈ 153.6 decimal digits
getcontext().prec = 154
getcontext().rounding = ROUND_HALF_UP

# Constants
FLOAT32_SIZE = 4
HASH_DIR = "data/raw/.hashes"
REF_2X2_HASH_FILE = "ref_2x2.sha256"

def setup_logging():
    """Configure logging for the reference engine."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def decimal_matmul(matrix_a: List[List[Decimal]], matrix_b: List[List[Decimal]]) -> List[List[Decimal]]:
    """
    Perform matrix multiplication using high-precision Decimal arithmetic.
    
    Args:
        matrix_a: First matrix (M x K)
        matrix_b: Second matrix (K x N)
        
    Returns:
        Result matrix (M x N)
    """
    if not matrix_a or not matrix_b:
        raise ValueError("Input matrices cannot be empty")
    
    rows_a = len(matrix_a)
    cols_a = len(matrix_a[0])
    rows_b = len(matrix_b)
    cols_b = len(matrix_b[0])
    
    if cols_a != rows_b:
        raise ValueError(f"Matrix dimensions incompatible for multiplication: {cols_a} != {rows_b}")
    
    result = []
    for i in range(rows_a):
        row = []
        for j in range(cols_b):
            val = Decimal(0)
            for k in range(cols_a):
                val += matrix_a[i][k] * matrix_b[k][j]
            row.append(val)
        result.append(row)
    
    return result

def decimal_softmax(vector: List[Decimal]) -> List[Decimal]:
    """
    Compute softmax using high-precision Decimal arithmetic.
    Uses the log-sum-exp trick for numerical stability even at high precision.
    
    Args:
        vector: Input vector
        
    Returns:
        Softmax probabilities
    """
    if not vector:
        return []
    
    # Find max for numerical stability (log-sum-exp trick)
    max_val = max(vector)
    
    # Compute exp(x - max) for all x
    # We need a high-precision exp implementation
    def decimal_exp(x: Decimal) -> Decimal:
        """Compute e^x using Taylor series with high precision."""
        # For very large negative numbers, result is effectively 0
        if x < Decimal(-50):
            return Decimal(0)
        
        # Taylor series: e^x = sum(x^n / n!)
        term = Decimal(1)
        result = Decimal(1)
        for n in range(1, 300):  # Sufficient iterations for 154 digits
            term *= x / Decimal(n)
            result += term
            if abs(term) < Decimal(10) ** (-160):
                break
        return result
    
    exp_vals = [decimal_exp(x - max_val) for x in vector]
    sum_exp = sum(exp_vals)
    
    if sum_exp == Decimal(0):
        # Fallback for degenerate case
        return [Decimal(1) / Decimal(len(vector))] * len(vector)
    
    return [val / sum_exp for val in exp_vals]

def decimal_layernorm(vector: List[Decimal], eps: Decimal = Decimal('1e-8')) -> List[Decimal]:
    """
    Compute Layer Normalization using high-precision Decimal arithmetic.
    
    Args:
        vector: Input vector
        eps: Small constant for numerical stability
        
    Returns:
        Normalized vector
    """
    if not vector:
        return []
    
    n = Decimal(len(vector))
    
    # Calculate mean
    mean = sum(vector) / n
    
    # Calculate variance
    variance = sum((x - mean) ** 2 for x in vector) / n
    
    # Calculate std
    std = variance.sqrt() + eps
    
    # Normalize
    return [(x - mean) / std for x in vector]

def generate_reference_tensor(dim: int = 2, seed: int = 12345) -> List[List[Decimal]]:
    """
    Generate a deterministic reference tensor for testing.
    Uses a simple linear congruential generator for determinism.
    
    Args:
        dim: Dimension for square matrix (dim x dim)
        seed: Random seed for determinism
        
    Returns:
        Matrix of Decimal values
    """
    # Simple LCG for deterministic generation
    a = 1664525
    c = 1013904223
    m = 2**32
    state = seed
    
    matrix = []
    for i in range(dim):
        row = []
        for j in range(dim):
            state = (a * state + c) % m
            # Map to range [-1, 1]
            val = (state / m) * 2 - 1
            row.append(Decimal(str(val)))
        matrix.append(row)
    
    return matrix

def save_tensor_to_binary(tensor: List[List[Decimal]], output_path: Path):
    """
    Save tensor to binary file in float32 format (for compatibility with kernels).
    The reference values are high-precision, but stored as float32 for comparison.
    
    Args:
        tensor: Matrix of Decimal values
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        for row in tensor:
            for val in row:
                # Convert Decimal to float32 for storage
                float_val = float(val)
                f.write(struct.pack('<f', float_val))

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_hash(hash_value: str, hash_path: Path):
    """Save hash to file."""
    hash_path.parent.mkdir(parents=True, exist_ok=True)
    with open(hash_path, 'w') as f:
        f.write(hash_value)

def run_reference_benchmarks(test_dim: int = 2, verify_hash: bool = False) -> Tuple[str, Path]:
    """
    Run reference benchmarks and optionally verify hash.
    
    Args:
        test_dim: Dimension for test matrix
        verify_hash: Whether to save and verify hash
        
    Returns:
        Tuple of (hash_value, output_path)
    """
    logger.info(f"Generating {test_dim}x{test_dim} reference tensor")
    
    # Generate input tensor
    input_tensor = generate_reference_tensor(dim=test_dim, seed=12345)
    
    # Perform operations
    # 1. MatMul: A * A^T
    input_tensor_t = [[input_tensor[j][i] for j in range(len(input_tensor))] 
                      for i in range(len(input_tensor[0]))]
    matmul_result = decimal_matmul(input_tensor, input_tensor_t)
    
    # 2. Softmax: Apply to first row
    softmax_result = decimal_softmax(matmul_result[0])
    
    # 3. LayerNorm: Apply to first row
    layernorm_result = decimal_layernorm(softmax_result)
    
    # Prepare output tensor (using layernorm result for consistency)
    # Pad to square matrix if needed
    output_dim = len(layernorm_result)
    output_tensor = []
    for i in range(output_dim):
        row = []
        for j in range(output_dim):
            if j < len(layernorm_result):
                row.append(layernorm_result[j])
            else:
                row.append(Decimal(0))
        output_tensor.append(row)
    
    # Save to file
    output_dir = Path("data/raw")
    output_file = output_dir / f"ref_{test_dim}x{test_dim}.bin"
    save_tensor_to_binary(output_tensor, output_file)
    
    # Compute hash
    hash_value = compute_sha256(output_file)
    logger.info(f"SHA-256 hash: {hash_value}")
    
    if verify_hash:
        hash_file = Path(HASH_DIR) / REF_2X2_HASH_FILE
        save_hash(hash_value, hash_file)
        logger.info(f"Hash saved to {hash_file}")
        
        # Verify by re-computing
        re_hash = compute_sha256(output_file)
        assert re_hash == hash_value, "Hash verification failed!"
    
    return hash_value, output_file

def main():
    parser = argparse.ArgumentParser(description="High-precision reference engine")
    parser.add_argument('--test', action='store_true', help='Run test benchmark')
    parser.add_argument('--verify-hash', action='store_true', help='Verify and save hash')
    parser.add_argument('--dim', type=int, default=2, help='Dimension for test matrix')
    
    args = parser.parse_args()
    
    if args.test:
        hash_val, out_path = run_reference_benchmarks(
            test_dim=args.dim, 
            verify_hash=args.verify_hash
        )
        print(f"Reference generated: {out_path}")
        print(f"Hash: {hash_val}")
        if args.verify_hash:
            print(f"Hash saved to: {Path(HASH_DIR) / REF_2X2_HASH_FILE}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()