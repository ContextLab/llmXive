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

def extract_2d_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts 2D descriptor features from the molecule dataframe.
    
    Since we are not using RDKit in this simplified version, we will compute
    basic graph-based features from the atom and coordinate data available.
    
    Output columns:
    - molecule_id: str
    - n_atoms: int
    - n_hydrogens: int
    - n_carbons: int
    - n_nitrogens: int
    - n_oxygens: int
    - n_fluorines: int
    - molecular_weight: float
    - dipole: float
    """
    results = []
    
    atomic_masses = {
        'H': 1.008, 'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998
    }
    
    for _, row in df.iterrows():
        mol_id = row['molecule_id']
        atoms = row['atoms']
        dipole = row['dipole']
        
        if not atoms:
            continue
        
        n_atoms = len(atoms)
        counts = {atom: atoms.count(atom) for atom in set(atoms)}
        
        # Ensure all counts exist
        n_h = counts.get('H', 0)
        n_c = counts.get('C', 0)
        n_n = counts.get('N', 0)
        n_o = counts.get('O', 0)
        n_f = counts.get('F', 0)
        
        # Calculate molecular weight
        mw = (n_h * atomic_masses['H'] +
              n_c * atomic_masses['C'] +
              n_n * atomic_masses['N'] +
              n_o * atomic_masses['O'] +
              n_f * atomic_masses['F'])
        
        results.append({
            'molecule_id': mol_id,
            'n_atoms': n_atoms,
            'n_hydrogens': n_h,
            'n_carbons': n_c,
            'n_nitrogens': n_n,
            'n_oxygens': n_o,
            'n_fluorines': n_f,
            'molecular_weight': mw,
            'dipole': dipole
        })
    
    return pd.DataFrame(results)
