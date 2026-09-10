"""
Deterministic synthetic tensor generator for LLM inference benchmarking.

Generates float32 tensors using fixed seeds and varied distributions (Normal, Uniform)
to ensure construct validity. Outputs binary files and SHA-256 hashes for verification.
"""
import os
import struct
import argparse
import hashlib
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Literal, Dict, Any, List

# Constants
DEFAULT_SEEDS = [12345, 67890, 11111]
DEFAULT_DIMENSION = 768  # Common hidden dimension size
DEFAULT_DISTRIBUTION = "normal"  # Options: "normal", "uniform"
OUTPUT_DIR = Path("data/raw")
HASHES_DIR = OUTPUT_DIR / ".hashes"
TENSOR_FORMAT = "<" + "f"  # Little-endian float32
TENSOR_HEADER_SIZE = 16  # 4 bytes for dim, 4 bytes for seed, 4 bytes for dist code, 4 bytes padding

def generate_tensor(
    seed: int,
    dim: int = DEFAULT_DIMENSION,
    distribution: Literal["normal", "uniform"] = DEFAULT_DISTRIBUTION
) -> Tuple[np.ndarray, str]:
    """
    Generate a deterministic tensor based on seed and distribution.
    
    Args:
        seed: Random seed for reproducibility.
        dim: Dimension of the square tensor (dim x dim).
        distribution: Type of distribution ('normal' or 'uniform').
        
    Returns:
        Tuple of (numpy array, distribution string identifier).
    """
    np.random.seed(seed)
    
    if distribution == "normal":
        tensor = np.random.normal(loc=0.0, scale=1.0, size=(dim, dim)).astype(np.float32)
    elif distribution == "uniform":
        tensor = np.random.uniform(low=-1.0, high=1.0, size=(dim, dim)).astype(np.float32)
    else:
        raise ValueError(f"Unsupported distribution: {distribution}")
        
    return tensor, distribution

def save_tensor_to_binary(tensor: np.ndarray, output_path: Path, seed: int, distribution: str) -> None:
    """
    Save tensor to a binary file with a custom header.
    
    Header format:
    - 4 bytes: dimension (int32)
    - 4 bytes: seed (int32)
    - 4 bytes: distribution code (0 for normal, 1 for uniform)
    - 4 bytes: padding
    - Rest: float32 data
    """
    dist_code = 0 if distribution == "normal" else 1
    
    with open(output_path, 'wb') as f:
        # Write header
        f.write(struct.pack("<i", tensor.shape[0]))
        f.write(struct.pack("<i", seed))
        f.write(struct.pack("<i", dist_code))
        f.write(struct.pack("<i", 0))  # padding
        
        # Write data
        f.write(tensor.tobytes())

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_hash(file_path: Path, hash_value: str) -> None:
    """Save hash to a .sha256 file."""
    with open(file_path, 'w') as f:
        f.write(hash_value + "\n")

def run_generation(
    seed: int,
    dim: int = DEFAULT_DIMENSION,
    distribution: Literal["normal", "uniform"] = DEFAULT_DISTRIBUTION,
    verify_hash: bool = False
) -> Dict[str, Any]:
    """
    Run the generation process for a specific seed.
    
    Args:
        seed: Random seed.
        dim: Tensor dimension.
        distribution: Distribution type.
        verify_hash: If True, check against existing hash and fail if mismatch.
        
    Returns:
        Dictionary with generation details.
    """
    # Ensure directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HASHES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate tensor
    tensor, dist_str = generate_tensor(seed, dim, distribution)
    
    # Define output paths
    output_filename = f"tensor_seed_{seed}_{dist_str}_{dim}x{dim}.bin"
    output_path = OUTPUT_DIR / output_filename
    hash_path = HASHES_DIR / f"{seed}.sha256"
    
    # Save tensor
    save_tensor_to_binary(tensor, output_path, seed, dist_str)
    
    # Compute hash
    file_hash = compute_sha256(output_path)
    
    # Verification logic
    if verify_hash and hash_path.exists():
        with open(hash_path, 'r') as f:
            stored_hash = f.read().strip()
        if stored_hash != file_hash:
            raise RuntimeError(
                f"Hash mismatch for seed {seed}! "
                f"Expected: {stored_hash}, Got: {file_hash}"
            )
        print(f"Hash verified for seed {seed}: {file_hash}")
    else:
        # Save new hash
        save_hash(hash_path, file_hash)
        print(f"Hash saved for seed {seed}: {file_hash}")
        
    # Print hash to stdout as required
    print(f"Generated tensor: {output_path}")
    print(f"SHA-256: {file_hash}")
    
    return {
        "seed": seed,
        "dimension": dim,
        "distribution": dist_str,
        "output_path": str(output_path),
        "hash": file_hash
    }

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic tensors for benchmarking."
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=False,
        help="Specific seed to generate. If not provided, runs default seeds."
    )
    parser.add_argument(
        "--dim",
        type=int,
        default=DEFAULT_DIMENSION,
        help=f"Tensor dimension (default: {DEFAULT_DIMENSION})"
    )
    parser.add_argument(
        "--distribution",
        type=str,
        choices=["normal", "uniform"],
        default=DEFAULT_DISTRIBUTION,
        help=f"Distribution type (default: {DEFAULT_DISTRIBUTION})"
    )
    parser.add_argument(
        "--verify-hash",
        action="store_true",
        help="Verify against existing hash file and fail if mismatch."
    )
    
    args = parser.parse_args()
    
    if args.seed is not None:
        # Single seed mode
        run_generation(
            seed=args.seed,
            dim=args.dim,
            distribution=args.distribution,
            verify_hash=args.verify_hash
        )
    else:
        # Batch mode: run all default seeds
        print(f"Running generation for default seeds: {DEFAULT_SEEDS}")
        for seed in DEFAULT_SEEDS:
            try:
                run_generation(
                    seed=seed,
                    dim=args.dim,
                    distribution=args.distribution,
                    verify_hash=args.verify_hash
                )
            except RuntimeError as e:
                print(f"Error processing seed {seed}: {e}")
                raise

if __name__ == "__main__":
    main()