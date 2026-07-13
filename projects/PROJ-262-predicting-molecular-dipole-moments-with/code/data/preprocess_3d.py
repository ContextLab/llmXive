from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Dict, Any
import sys
from pathlib import Path

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def extract_3d_features(molecule_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 3D features from the molecule dataframe.
    Expected columns in molecule_df: 'molecule_id', 'atoms', 'coordinates', 'dipole'
    Returns a dataframe with 'molecule_id', 'features_3d' (flattened coordinates + atom types), 'dipole'
    """
    features_list = []
    
    for _, row in molecule_df.iterrows():
        mol_id = row['molecule_id']
        atoms = row['atoms']
        coords = row['coordinates']
        dipole = row['dipole']
        
        # Flatten coordinates and atom types
        # atoms: list of atom types (e.g., [6, 8, 1, ...])
        # coords: list of [x, y, z]
        
        atom_array = np.array(atoms)
        coord_array = np.array(coords).flatten()
        
        # Combine atom types and coordinates
        # Normalize atom types if necessary (e.g., one-hot or embedding)
        # For simplicity, we use the atomic number as a feature
        feature_vector = np.concatenate([atom_array.astype(float), coord_array])
        
        features_list.append({
            'molecule_id': mol_id,
            'features_3d': [float(x) for x in feature_vector],
            'dipole': float(dipole)
        })
    
    return pd.DataFrame(features_list)
