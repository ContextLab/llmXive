import os
import struct
import argparse
import numpy as np
from typing import Tuple, Optional, Literal, Dict, Any, List

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
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--distributions", type=str, default="normal;uniform",
                        help="Semicolon separated list of distributions (normal, uniform)")
    
    args = parser.parse_args()
    
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