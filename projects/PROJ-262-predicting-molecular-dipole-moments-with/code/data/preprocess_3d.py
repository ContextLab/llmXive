from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Dict, Any
import sys
from pathlib import Path

# Ensure we can import from project root if needed, though usually 
# this file is run from the code directory.
# No external heavy imports required for this mock implementation 
# as we assume QM9 data structure is known.

def extract_3d_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 3D features from the molecule DataFrame.
    
    Expected Input Columns (from QM9):
    - molecule_id: str
    - atom_numbers: list of int (or similar representation)
    - coordinates: list of [x, y, z] per atom
    - dipole_magnitude: float (target)
    
    Output Columns:
    - molecule_id: str
    - features_3d: list of float (flattened coordinates + atom embeddings)
    - dipole_magnitude: float
    """
    if df.empty:
        return pd.DataFrame()

    # Mocking the extraction logic to ensure it runs without heavy 3D libraries
    # if they aren't installed, while still producing real data structures.
    # In a real scenario, this would use RDKit or similar to process coordinates.
    
    processed_rows = []
    
    for idx, row in df.iterrows():
        mol_id = row.get('molecule_id', f'mol_{idx}')
        
        # Safely access coordinates and atom numbers
        coords = row.get('coordinates', [])
        atom_nums = row.get('atom_numbers', [])
        dipole = row.get('dipole_magnitude', 0.0)
        
        # Flatten coordinates: [x1, y1, z1, x2, y2, z2, ...]
        flat_coords = []
        if isinstance(coords, list):
            for c in coords:
                if isinstance(c, (list, tuple)):
                    flat_coords.extend([float(v) for v in c])
                else:
                    # Handle case where coords might be a string representation
                    # or already flat
                    flat_coords.append(float(c))
        
        # Simple atom embedding: normalize atomic number or one-hot
        # Here we just use the atomic number normalized by max (100)
        atom_features = []
        if isinstance(atom_nums, list):
            for a in atom_nums:
                atom_features.append(float(a) / 100.0)
        
        # Combine features
        features_3d = flat_coords + atom_features
        
        # Pad or truncate to a fixed size if necessary (e.g., max 20 atoms)
        # For this implementation, we keep variable length but ensure it's serializable
        # Parquet supports lists.
        
        processed_rows.append({
            'molecule_id': mol_id,
            'features_3d': features_3d,
            'dipole_magnitude': float(dipole)
        })
    
    result_df = pd.DataFrame(processed_rows)
    
    # Validate no NaNs in critical columns
    if result_df['features_3d'].isnull().any():
        print("Warning: NaN found in features_3d column. Filling with zeros.")
        result_df['features_3d'] = result_df['features_3d'].apply(lambda x: [0.0] if pd.isna(x) else x)
        
    return result_df
