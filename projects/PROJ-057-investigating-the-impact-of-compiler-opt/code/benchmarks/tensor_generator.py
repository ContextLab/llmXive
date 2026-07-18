import os
import struct
import argparse
import hashlib
import numpy as np
from typing import Tuple, Optional, Literal, Dict, Any, List

# Fixed seeds as per task requirement
FIXED_SEEDS = [12345, 67890, 11111]

def generate_tensor(
    shape: Tuple[int, int],
    dtype: str = "float32",
    distribution: Literal["normal", "uniform"] = "normal",
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generates a deterministic synthetic tensor.
    
    Args:
        shape: Tuple of (rows, cols)
        dtype: Data type string (default "float32")
        distribution: Either "normal" or "uniform"
        seed: Random seed for reproducibility. If None, no seed is set.
    
    Returns:
        numpy array of the specified shape and distribution.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if distribution == "normal":
        data = np.random.randn(*shape).astype(np.float32)
    elif distribution == "uniform":
        data = np.random.uniform(-1.0, 1.0, size=shape).astype(np.float32)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")
    
    return data

def save_tensor_to_binary(tensor: np.ndarray, path: str):
    """
    Saves a numpy array to a binary file.
    
    Format:
        4 bytes: rows (uint32)
        4 bytes: cols (uint32)
        N bytes: raw float32 data
    """
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(path, "wb") as f:
        # Write shape first
        f.write(struct.pack('I', tensor.shape[0]))
        f.write(struct.pack('I', tensor.shape[1]))
        # Write data
        f.write(tensor.tobytes())

def compute_sha256(file_path: str) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_hash(hash_value: str, seed: int, output_dir: str):
    """Saves the hash to the specified location."""
    hash_dir = os.path.join(output_dir, ".hashes")
    os.makedirs(hash_dir, exist_ok=True)
    hash_file = os.path.join(hash_dir, f"{seed}.sha256")
    with open(hash_file, "w") as f:
        f.write(hash_value)

def run_generation(
    shapes: List[Tuple[int, int]],
    output_dir: str = "data/raw",
    seed: int = 42,
    distributions: List[str] = None
) -> Dict[str, str]:
    """
    Generates and saves tensors for benchmarking.
    
    Args:
        shapes: List of (rows, cols) tuples
        output_dir: Directory to save output files
        seed: Base random seed
        distributions: List of distribution types to use. 
                     If provided, cycles through them. If None, defaults to ['normal', 'uniform'].
    
    Returns:
        Dictionary mapping filename to full path.
    """
    if distributions is None:
        distributions = ["normal", "uniform"]
    
    os.makedirs(output_dir, exist_ok=True)
    outputs = {}
    
    for i, shape in enumerate(shapes):
        # Cycle through distributions to ensure varied distributions are used
        dist = distributions[i % len(distributions)]
        tensor = generate_tensor(shape, distribution=dist, seed=seed + i)
        
        filename = f"tensor_{shape[0]}x{shape[1]}_{dist}_seed{seed+i}.bin"
        path = os.path.join(output_dir, filename)
        save_tensor_to_binary(tensor, path)
        outputs[filename] = path
    
    return outputs

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic tensors.")
    parser.add_argument("--shapes", type=str, default="768,768;512,512",
                        help="Semicolon separated list of shapes (e.g., 768,768;512,512)")
    parser.add_argument("--output-dir", type=str, default="data/raw",
                        help="Directory to save output files")
    parser.add_argument("--seed", type=int, default=None,
                        help="Specific seed to use. If provided, uses that seed for a single tensor generation.")
    parser.add_argument("--distribution", type=str, default="normal",
                        help="Distribution type: 'normal' or 'uniform'. Used if --seed is provided.")
    parser.add_argument("--verify-hash", action="store_true",
                        help="Generate the file, compute its SHA-256 hash, print it, and save it to data/raw/.hashes/<SEED>.sha256")
    
    args = parser.parse_args()
    
    if args.seed is not None:
        # Single generation mode for verification
        if args.distribution not in ["normal", "uniform"]:
            raise ValueError(f"Invalid distribution: {args.distribution}. Must be 'normal' or 'uniform'.")
        
        # Use a default shape if not specified for single mode, or parse a single shape from --shapes if needed
        # For this task, we assume a standard benchmark shape for verification if only seed is given
        shape = (512, 512) 
        
        tensor = generate_tensor(shape, distribution=args.distribution, seed=args.seed)
        filename = f"tensor_{shape[0]}x{shape[1]}_{args.distribution}_seed{args.seed}.bin"
        path = os.path.join(args.output_dir, filename)
        
        save_tensor_to_binary(tensor, path)
        
        # Compute and save hash
        hash_val = compute_sha256(path)
        print(f"SHA-256 Hash for seed {args.seed}: {hash_val}")
        save_hash(hash_val, args.seed, args.output_dir)
        
        print(f"Tensor generated: {path}")
    else:
        # Batch generation mode (original behavior)
        # Parse shapes
        shapes = []
        for shape_str in args.shapes.split(";"):
            dims = [int(x.strip()) for x in shape_str.split(",")]
            if len(dims) == 2:
                shapes.append(tuple(dims))
            else:
                raise ValueError(f"Invalid shape: {shape_str}")
        
        # Parse distributions
        distributions = [d.strip().lower() for d in args.distributions.split(";")]
        for d in distributions:
            if d not in ["normal", "uniform"]:
                raise ValueError(f"Invalid distribution: {d}. Must be 'normal' or 'uniform'.")
        
        results = run_generation(shapes, args.output_dir, args.seed, distributions)
        
        print("Tensor generation complete:")
        for name, path in results.items():
            print(f"  {name}: {path}")

if __name__ == "__main__":
    main()