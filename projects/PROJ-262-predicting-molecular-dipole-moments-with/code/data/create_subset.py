from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional
import sys
from pathlib import Path
import tarfile
import random
import hashlib

def create_reproducible_subset(raw_data_path: Path, output_path: Path, size: int, seed: int):
    """
    Creates a reproducible random subset of the QM9 dataset.
    
    This function loads the QM9 .npz file, selects a deterministic subset of molecules
    based on the provided seed, and writes a Parquet file containing the molecule IDs
    and their original indices. The actual feature extraction (3D/2D) is handled by
    downstream tasks (T017, T018) which will use these indices.
    
    Args:
        raw_data_path: Path to the directory containing the QM9 .npz file or the file itself.
        output_path: Path where the output parquet file will be written.
        size: Number of molecules to include in the subset.
        seed: Random seed for reproducibility.
    """
    # Set seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    # Locate the QM9 data file (usually 'qm9.npz' or similar)
    npz_file = None
    if raw_data_path.is_dir():
        # Look for common QM9 file names
        candidates = list(raw_data_path.glob("*.npz")) + list(raw_data_path.glob("*.npy"))
        if not candidates:
            raise FileNotFoundError(f"No data files (.npz, .npy) found in {raw_data_path}")
        npz_file = candidates[0]
    else:
        npz_file = raw_data_path
    
    print(f"Loading {npz_file} to determine dataset size...")
    try:
        data = np.load(npz_file, allow_pickle=True)
        
        # Handle different storage formats in QM9 npz
        if isinstance(data, np.ndarray) and data.dtype == object:
            raw_data = data[0] if len(data) > 0 else data
        else:
            raw_data = data
        
        # Extract molecule count
        if isinstance(raw_data, dict):
            # QM9 usually stores 'atom_numbers' or 'Z'
            atom_numbers = raw_data.get('atom_numbers')
            if atom_numbers is None and 'Z' in raw_data:
                atom_numbers = raw_data['Z']
            
            if atom_numbers is None:
                # Fallback: try to find any array with shape[0] representing molecules
                for key, val in raw_data.items():
                    if hasattr(val, 'shape') and len(val.shape) > 0:
                        atom_numbers = val
                        break
            
            if atom_numbers is None:
                raise KeyError("Cannot determine molecule count from dataset keys: " + str(list(raw_data.keys())))
            
            n_molecules = atom_numbers.shape[0]
        else:
            # Fallback for structured arrays or direct access
            n_molecules = len(data)
            
    except Exception as e:
        print(f"Error loading {npz_file}: {e}", file=sys.stderr)
        # Fallback to standard QM9 size if loading fails, but warn loudly
        print("Warning: Assuming standard QM9 size of 133,885 molecules.", file=sys.stderr)
        n_molecules = 133885

    print(f"Total molecules in dataset: {n_molecules}")
    
    if size > n_molecules:
        print(f"Requested size {size} exceeds dataset size {n_molecules}. Using all.")
        size = n_molecules
    
    # Generate deterministic random indices
    indices = np.random.choice(n_molecules, size=size, replace=False)
    indices.sort() # Sort for consistent ordering
    
    # Create DataFrame with molecule_id and original_index
    # The molecule_id is formatted as "qm9_{index}" to match downstream expectations
    df = pd.DataFrame({
        'molecule_id': [f"qm9_{int(i)}" for i in indices],
        'original_index': indices
    })
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing subset of {size} molecules to {output_path}...")
    df.to_parquet(output_path, index=False)
    print("Subset created successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create a reproducible subset of QM9 data.")
    parser.add_argument("--raw", type=str, required=True, help="Path to raw QM9 data (dir or file)")
    parser.add_argument("--output", type=str, required=True, help="Path for output parquet file")
    parser.add_argument("--size", type=int, default=5000, help="Number of molecules in subset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    create_reproducible_subset(
        raw_data_path=Path(args.raw),
        output_path=Path(args.output),
        size=args.size,
        seed=args.seed
    )