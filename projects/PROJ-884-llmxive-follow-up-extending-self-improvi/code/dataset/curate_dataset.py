"""
Curates the dataset by generating puzzles and computing checksums.
This file is extended to ensure it can be used by the validation pipeline.
"""
import json
import hashlib
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import the generator
try:
    from code.dataset.generator import PuzzleGenerator, PuzzleType
except ImportError:
    # Fallback for direct execution context
    from dataset.generator import PuzzleGenerator, PuzzleType

def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_puzzles(
    n_values: List[int],
    count: int,
    types: List[str],
    output_dir: Path,
    seed: int = 42
) -> Path:
    """
    Generate puzzles for given N values and count, saving to output_dir.
    Returns the path to the generated JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "puzzles.json"
    
    generator = PuzzleGenerator(seed=seed)
    all_puzzles = []
    
    for n in n_values:
        for t_str in types:
            try:
                p_type = PuzzleType[t_str.upper()]
                puzzles = generator.generate_batch(n, count, p_type)
                all_puzzles.extend(puzzles)
                print(f"Generated {len(puzzles)} puzzles for N={n}, Type={t_str}")
            except KeyError:
                print(f"Warning: Unknown puzzle type {t_str}, skipping.")
    
    with open(output_file, 'w') as f:
        json.dump(all_puzzles, f, indent=2)
    
    checksum = compute_checksum(output_file)
    print(f"Generated {len(all_puzzles)} puzzles. Checksum: {checksum}")
    return output_file

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Curate dataset")
    parser.add_argument("--n", type=int, nargs="+", default=[10, 50, 100], help="N values")
    parser.add_argument("--count", type=int, default=10, help="Count per N/Type")
    parser.add_argument("--types", type=str, nargs="+", default=["sudoku"], help="Puzzle types")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    output_path = generate_puzzles(
        args.n, args.count, args.types, Path(args.output_dir), args.seed
    )
    print(f"Dataset curated at: {output_path}")

if __name__ == "__main__":
    main()
