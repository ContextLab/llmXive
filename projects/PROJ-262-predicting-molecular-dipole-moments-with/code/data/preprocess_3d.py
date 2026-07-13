from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Dict, Any

# Ensure project root is in path
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def extract_3d_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts 3D coordinate features from the molecule dataframe.
    
    Expected input columns:
    - molecule_id: str
    - atoms: list of atom symbols
    - coordinates: list of [x, y, z] floats
    - dipole: float (target)
    
    Output columns:
    - molecule_id: str
    - n_atoms: int
    - center_of_mass_x, center_of_mass_y, center_of_mass_z: float
    - max_distance: float
    - dipole: float
    """
    results = []
    
    for _, row in df.iterrows():
        mol_id = row['molecule_id']
        atoms = row['atoms']
        coords = row['coordinates']
        dipole = row['dipole']
        
        if not coords or len(coords) == 0:
            continue
            
        coords_array = np.array(coords)
        n_atoms = len(atoms)
        
        # Calculate center of mass (assuming equal mass for simplicity or using atomic masses)
        # For QM9, we can approximate or use standard atomic masses
        atomic_masses = {
            'H': 1.008, 'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998
        }
        masses = np.array([atomic_masses.get(a, 12.011) for a in atoms])
        
        center_of_mass = np.average(coords_array, axis=0, weights=masses)
        
        # Calculate max distance from center of mass
        distances = np.linalg.norm(coords_array - center_of_mass, axis=1)
        max_distance = float(np.max(distances))
        
        results.append({
            'molecule_id': mol_id,
            'n_atoms': n_atoms,
            'center_of_mass_x': float(center_of_mass[0]),
            'center_of_mass_y': float(center_of_mass[1]),
            'center_of_mass_z': float(center_of_mass[2]),
            'max_distance': max_distance,
            'dipole': dipole
        })
    
    return pd.DataFrame(results)
