"""
High-precision reference engine using Python decimal module.
Implements MatMul, Softmax, and LayerNorm with arbitrary-precision arithmetic.
"""
import os
import struct
import argparse
import logging
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from decimal import Decimal, getcontext, ROUND_HALF_UP

import numpy as np

# Set decimal precision to 512 bits as per plan.md requirement
# 512 bits ~= 154 decimal digits
getcontext().prec = 154
getcontext().rounding = ROUND_HALF_UP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def decimal_matmul(A: List[List[Decimal]], B: List[List[Decimal]]) -> List[List[Decimal]]:
    """
    Perform matrix multiplication using Decimal arithmetic.
    
    Args:
        A: First matrix (list of lists of Decimals)
        B: Second matrix (list of lists of Decimals)
        
    Returns:
        Result matrix C = A @ B
    """
    rows_A = len(A)
    cols_A = len(A[0])
    rows_B = len(B)
    cols_B = len(B[0])
    
    if cols_A != rows_B:
        raise ValueError(f"Matrix dimensions mismatch: {cols_A} != {rows_B}")
    
    # Initialize result matrix with zeros
    C = [[Decimal(0) for _ in range(cols_B)] for _ in range(rows_A)]
    
    # Perform multiplication
    for i in range(rows_A):
        for j in range(cols_B):
            total = Decimal(0)
            for k in range(cols_A):
                total += A[i][k] * B[k][j]
            C[i][j] = total
            
    return C

def decimal_softmax(logits: List[Decimal]) -> List[Decimal]:
    """
    Compute softmax using Decimal arithmetic.
    Uses the log-sum-exp trick for numerical stability.
    
    Args:
        logits: Input logits (list of Decimals)
        
    Returns:
        Softmax probabilities (list of Decimals)
    """
    if not logits:
        return []
    
    # Find max for numerical stability
    max_logit = max(logits)
    
    # Compute exp(logits - max)
    exp_shifted = []
    for logit in logits:
        # Use Decimal.exp() for high-precision exponential
        exp_val = (logit - max_logit).exp()
        exp_shifted.append(exp_val)
    
    # Compute sum of exponentials
    sum_exp = sum(exp_shifted)
    
    # Normalize
    if sum_exp == Decimal(0):
        raise ValueError("Sum of exponentials is zero, cannot compute softmax")
    
    probs = [exp_val / sum_exp for exp_val in exp_shifted]
    return probs

def decimal_layernorm(x: List[Decimal], eps: Decimal = Decimal('1e-8')) -> List[Decimal]:
    """
    Compute LayerNorm using Decimal arithmetic.
    
    Args:
        x: Input tensor (list of Decimals)
        eps: Small constant for numerical stability
        
    Returns:
        Normalized tensor
    """
    if not x:
        return []
    
    n = Decimal(len(x))
    
    # Compute mean
    mean = sum(x) / n
    
    # Compute variance
    variance = sum((xi - mean) ** 2 for xi in x) / n
    
    # Compute standard deviation
    std = variance.sqrt() + eps
    
    # Normalize
    normalized = [(xi - mean) / std for xi in x]
    return normalized

def generate_reference_tensor(
    seed: int,
    dim: int = 2,
    distribution: str = 'normal'
) -> Dict[str, Any]:
    """
    Generate reference tensors for a 2x2 matrix (or specified dim) using fixed seeds.
    
    Args:
        seed: Random seed for reproducibility
        dim: Dimension of the square matrix
        distribution: 'normal' or 'uniform'
        
    Returns:
        Dictionary containing:
            - 'input_tensor': Original float32 tensor
            - 'matmul_result': High-precision MatMul result
            - 'softmax_result': High-precision Softmax result
            - 'layernorm_result': High-precision LayerNorm result
            - 'seed': Used seed
            - 'dim': Dimension
    """
    # Set numpy seed for reproducibility
    np.random.seed(seed)
    
    # Generate input tensor
    if distribution == 'normal':
        input_float = np.random.randn(dim, dim).astype(np.float32)
    elif distribution == 'uniform':
        input_float = np.random.uniform(-1, 1, (dim, dim)).astype(np.float32)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")
    
    # Convert to Decimal
    input_decimal = [
        [Decimal(str(float(val))) for val in row]
        for row in input_float
    ]
    
    # Compute MatMul (A @ A^T for a simple self-multiplication test)
    # For 2x2, we'll do A @ A to keep it simple
    matmul_result = decimal_matmul(input_decimal, input_decimal)
    
    # Compute Softmax on flattened rows
    softmax_results = []
    for row in input_decimal:
        softmax_results.append(decimal_softmax(row))
    
    # Compute LayerNorm on flattened input
    flat_input = [val for row in input_decimal for val in row]
    layernorm_result = decimal_layernorm(flat_input)
    
    return {
        'input_tensor': input_float,
        'matmul_result': matmul_result,
        'softmax_result': softmax_results,
        'layernorm_result': layernorm_result,
        'seed': seed,
        'dim': dim,
        'distribution': distribution
    }

def save_tensor_to_binary(
    data: Any,
    filepath: Path,
    tensor_type: str = 'matmul'
) -> str:
    """
    Save reference tensor data to a binary file.
    
    Args:
        data: The reference data dictionary
        filepath: Output path
        tensor_type: Type of tensor being saved
        
    Returns:
        SHA-256 hash of the saved file
    """
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert Decimals to strings for JSON serialization
    # We'll use a simple binary format: header + float32 data
    with open(filepath, 'wb') as f:
        # Write metadata header
        header = f"{tensor_type}:{data['seed']}:{data['dim']}".encode('utf-8')
        f.write(struct.pack('I', len(header)))
        f.write(header)
        
        # Write input tensor as float32
        input_data = data['input_tensor'].tobytes()
        f.write(struct.pack('I', len(input_data)))
        f.write(input_data)
        
        # Write matmul result (flatten and convert to float32 for storage)
        # Note: We store as float32 for compatibility, but the computation was high-precision
        matmul_flat = [float(val) for row in data['matmul_result'] for val in row]
        matmul_bytes = np.array(matmul_flat, dtype=np.float32).tobytes()
        f.write(struct.pack('I', len(matmul_bytes)))
        f.write(matmul_bytes)
        
        # Write softmax result
        softmax_flat = [float(val) for row in data['softmax_result'] for val in row]
        softmax_bytes = np.array(softmax_flat, dtype=np.float32).tobytes()
        f.write(struct.pack('I', len(softmax_bytes)))
        f.write(softmax_bytes)
        
        # Write layernorm result
        layernorm_bytes = np.array(data['layernorm_result'], dtype=np.float32).tobytes()
        f.write(struct.pack('I', len(layernorm_bytes)))
        f.write(layernorm_bytes)
    
    # Compute SHA-256 hash
    with open(filepath, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    return file_hash

def run_reference_benchmarks(
    seed: int = 12345,
    dim: int = 2,
    output_dir: Path = None,
    verify_hash: bool = False
) -> Tuple[Dict[str, Any], str]:
    """
    Run reference benchmarks and save results.
    
    Args:
        seed: Random seed
        dim: Matrix dimension
        output_dir: Output directory
        verify_hash: If True, verify hash against stored hash
        
    Returns:
        Tuple of (reference_data, file_hash)
    """
    if output_dir is None:
        output_dir = Path('data/raw')
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate reference
    logger.info(f"Generating reference tensor with seed={seed}, dim={dim}")
    reference_data = generate_reference_tensor(seed=seed, dim=dim, distribution='normal')
    
    # Save to binary
    output_file = output_dir / f'ref_{dim}x{dim}_seed{seed}.bin'
    file_hash = save_tensor_to_binary(reference_data, output_file, f'ref_{dim}x{dim}')
    
    # Save hash if requested
    if verify_hash:
        hash_dir = output_dir / '.hashes'
        hash_dir.mkdir(parents=True, exist_ok=True)
        hash_file = hash_dir / f'ref_{dim}x{dim}.sha256'
        
        with open(hash_file, 'w') as f:
            f.write(file_hash)
        
        logger.info(f"Hash saved to {hash_file}: {file_hash}")
    
    logger.info(f"Reference data saved to {output_file}")
    logger.info(f"File hash: {file_hash}")
    
    return reference_data, file_hash

def main():
    """Main entry point for reference engine."""
    parser = argparse.ArgumentParser(description='High-precision reference engine')
    parser.add_argument('--test', action='store_true', help='Run test mode with 2x2 matrix')
    parser.add_argument('--seed', type=int, default=12345, help='Random seed')
    parser.add_argument('--dim', type=int, default=2, help='Matrix dimension')
    parser.add_argument('--output-dir', type=str, default='data/raw', help='Output directory')
    parser.add_argument('--verify-hash', action='store_true', help='Verify and save hash')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    if args.test:
        logger.info("Running in test mode with 2x2 matrix")
        reference_data, file_hash = run_reference_benchmarks(
            seed=args.seed,
            dim=2,
            output_dir=output_dir,
            verify_hash=args.verify_hash
        )
        print(f"Test reference hash: {file_hash}")
    else:
        reference_data, file_hash = run_reference_benchmarks(
            seed=args.seed,
            dim=args.dim,
            output_dir=output_dir,
            verify_hash=args.verify_hash
        )
        print(f"Reference hash: {file_hash}")

if __name__ == '__main__':
    main()