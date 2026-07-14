from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional
import sys
from pathlib import Path
import tarfile
import random

def create_reproducible_subset(raw_data_path: Path, output_path: Path, size: int, seed: int):
    """
    Creates a reproducible random subset of the QM9 dataset.
    
    Since QM9 is binary (.npz), we first need to load the molecule IDs (indices)
    and then select a subset. We assume the raw_data_path points to the directory
    containing the extracted QM9 files.
    
    We will generate a CSV with molecule_id (index) and placeholders for data that
    will be filled by the 3D/2D extraction steps.
    """
    # Set seed
    random.seed(seed)
    np.random.seed(seed)
    
    # Determine total number of molecules
    # We need to find the .npz file again to count molecules
    npz_file = None
    if raw_data_path.is_dir():
        candidates = list(raw_data_path.glob("*.npz")) + list(raw_data_path.glob("*.npy"))
        if not candidates:
            raise FileNotFoundError(f"No data files found in {raw_data_path}")
        npz_file = candidates[0]
    else:
        npz_file = raw_data_path
    
    print(f"Loading {npz_file} to determine dataset size...")
    try:
        data = np.load(npz_file, allow_pickle=True)
        if isinstance(data, np.ndarray) and data.dtype == object:
            raw_data = data[0] if len(data) > 0 else data
        else:
            raw_data = data
        
        if isinstance(raw_data, dict):
            atom_numbers = raw_data.get('atom_numbers')
            if atom_numbers is None and 'Z' in raw_data:
                atom_numbers = raw_data['Z']
            if atom_numbers is None:
                raise KeyError("Cannot find atom_numbers")
            n_molecules = atom_numbers.shape[0]
        else:
            # Fallback for structured arrays
            n_molecules = len(data)
    except Exception as e:
        print(f"Warning: Could not determine dataset size from {npz_file}: {e}", file=sys.stderr)
        print("Assuming standard QM9 size of 133,885 molecules.", file=sys.stderr)
        n_molecules = 133885

    print(f"Total molecules in dataset: {n_molecules}")
    
    if size > n_molecules:
        print(f"Requested size {size} exceeds dataset size {n_molecules}. Using all.")
        size = n_molecules
    
    # Generate random indices
    indices = np.random.choice(n_molecules, size=size, replace=False)
    indices.sort() # Sort for reproducibility in reading if needed
    
    # Create a simple CSV with molecule_id (index)
    # The downstream steps will use these indices to fetch actual data from the .npz
    df = pd.DataFrame({
        'molecule_id': [f"qm9_{int(i)}" for i in indices],
        'original_index': indices
    })
    
    print(f"Writing subset of {size} molecules to {output_path}...")
    df.to_csv(output_path, index=False)
    print("Subset created successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--size", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    create_reproducible_subset(Path(args.raw), Path(args.output), args.size, args.seed)
