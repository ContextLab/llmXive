import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from chemparse import Composition
import numpy as np
from collections import defaultdict

# Import logger from the project root package if available, otherwise create a local one
try:
    from . import logger
except ImportError:
    import logging as local_logging
    logger = local_logging.getLogger(__name__)

# Periodic Table Data (Element -> Atomic Radius in pm, Electronegativity (Pauling), Valence Electrons)
# Source: Standard periodic table values. Approximated for common ceramic elements.
PERIODIC_DATA = {
    # Anions
    'O': {'radius': 60.0, 'electronegativity': 3.44, 'valence': 6},
    'N': {'radius': 65.0, 'electronegativity': 3.04, 'valence': 5},
    'C': {'radius': 70.0, 'electronegativity': 2.55, 'valence': 4},
    'F': {'radius': 50.0, 'electronegativity': 3.98, 'valence': 7},
    'S': {'radius': 100.0, 'electronegativity': 2.58, 'valence': 6},
    'Cl': {'radius': 99.0, 'electronegativity': 3.16, 'valence': 7},
    
    # Cations - Group 1
    'Li': {'radius': 76.0, 'electronegativity': 0.98, 'valence': 1},
    'Na': {'radius': 102.0, 'electronegativity': 0.93, 'valence': 1},
    'K': {'radius': 138.0, 'electronegativity': 0.82, 'valence': 1},
    'Rb': {'radius': 152.0, 'electronegativity': 0.82, 'valence': 1},
    'Cs': {'radius': 167.0, 'electronegativity': 0.79, 'valence': 1},
    
    # Cations - Group 2
    'Be': {'radius': 45.0, 'electronegativity': 1.57, 'valence': 2},
    'Mg': {'radius': 72.0, 'electronegativity': 1.31, 'valence': 2},
    'Ca': {'radius': 100.0, 'electronegativity': 1.00, 'valence': 2},
    'Sr': {'radius': 118.0, 'electronegativity': 0.95, 'valence': 2},
    'Ba': {'radius': 135.0, 'electronegativity': 0.89, 'valence': 2},
    
    # Transition Metals & Others
    'Al': {'radius': 53.0, 'electronegativity': 1.61, 'valence': 3},
    'Sc': {'radius': 88.5, 'electronegativity': 1.36, 'valence': 3},
    'Ti': {'radius': 86.0, 'electronegativity': 1.54, 'valence': 4},
    'V': {'radius': 79.0, 'electronegativity': 1.63, 'valence': 5},
    'Cr': {'radius': 80.0, 'electronegativity': 1.66, 'valence': 6},
    'Mn': {'radius': 83.0, 'electronegativity': 1.55, 'valence': 7},
    'Fe': {'radius': 79.0, 'electronegativity': 1.83, 'valence': 8}, # Variable, using common
    'Co': {'radius': 74.5, 'electronegativity': 1.88, 'valence': 9},
    'Ni': {'radius': 69.0, 'electronegativity': 1.91, 'valence': 10},
    'Cu': {'radius': 77.0, 'electronegativity': 1.90, 'valence': 11},
    'Zn': {'radius': 74.0, 'electronegativity': 1.65, 'valence': 12},
    'Zr': {'radius': 86.0, 'electronegativity': 1.33, 'valence': 4},
    'Nb': {'radius': 78.0, 'electronegativity': 1.60, 'valence': 5},
    'Mo': {'radius': 79.0, 'electronegativity': 2.16, 'valence': 6},
    'Hf': {'radius': 85.0, 'electronegativity': 1.30, 'valence': 4},
    'Ta': {'radius': 86.0, 'electronegativity': 1.50, 'valence': 5},
    'W': {'radius': 86.0, 'electronegativity': 2.36, 'valence': 6},
    'Si': {'radius': 111.0, 'electronegativity': 1.90, 'valence': 4},
    'P': {'radius': 107.0, 'electronegativity': 2.19, 'valence': 5},
    'Sn': {'radius': 112.0, 'electronegativity': 1.96, 'valence': 4},
    'Y': {'radius': 104.0, 'electronegativity': 1.22, 'valence': 3},
    'La': {'radius': 117.0, 'electronegativity': 1.10, 'valence': 3},
    'Ce': {'radius': 103.0, 'electronegativity': 1.12, 'valence': 4},
    'Gd': {'radius': 105.0, 'electronegativity': 1.20, 'valence': 3},
    'In': {'radius': 112.0, 'electronegativity': 1.78, 'valence': 3},
    'Ga': {'radius': 122.0, 'electronegativity': 1.81, 'valence': 3},
}

def _parse_composition_to_atoms(composition_str: str) -> Dict[str, float]:
    """
    Parses a composition string (e.g., 'Al2O3') into a dictionary of element counts.
    Returns a dict: { 'Al': 2.0, 'O': 3.0 }
    """
    try:
        comp = Composition(composition_str)
        # chemparse returns a dict like {'Al': 2, 'O': 3} or {'Al2': 1, 'O3': 1} if not normalized
        # We assume normalized or standard format. If chemparse returns complex keys, we handle them.
        # Standard chemparse output for 'Al2O3' is {'Al': 2.0, 'O': 3.0}
        atoms = {}
        for elem, count in comp.items():
            # Ensure the key is the element symbol
            atoms[elem] = float(count)
        return atoms
    except Exception as e:
        logger.warning(f"Failed to parse composition '{composition_str}': {e}")
        return {}

def _get_property_safe(element: str, prop: str, default: float = 0.0) -> float:
    """Safely get a property from PERIODIC_DATA, returning default if missing."""
    if element in PERIODIC_DATA:
        return PERIODIC_DATA[element].get(prop, default)
    # Handle missing elements by logging and returning 0 or raising if critical
    # For robustness in this pipeline, we return 0 and let downstream handle NaNs if strict
    logger.warning(f"Element '{element}' not found in periodic data table. Using default 0.0.")
    return default

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes elemental descriptors for the ceramic dataset.
    
    Calculates:
    1. Mean Atomic Radius (weighted by atom count)
    2. Electronegativity Standard Deviation (weighted)
    3. Cation Size Variance (variance of cation radii)
    4. Valence Electron Concentration (VEC)
    
    Args:
        df: DataFrame with at least a 'composition' column.
        
    Returns:
        DataFrame with new descriptor columns appended.
    """
    logger.info("Starting descriptor computation...")
    
    descriptors = []
    
    for idx, row in df.iterrows():
        comp_str = row.get('composition', '')
        if not comp_str:
            # Append NaNs for this row
            descriptors.append({
                'mean_atomic_radius': np.nan,
                'electronegativity_std': np.nan,
                'cation_size_variance': np.nan,
                'valence_electron_concentration': np.nan
            })
            continue
        
        atoms = _parse_composition_to_atoms(comp_str)
        if not atoms:
            descriptors.append({
                'mean_atomic_radius': np.nan,
                'electronegativity_std': np.nan,
                'cation_size_variance': np.nan,
                'valence_electron_concentration': np.nan
            })
            continue
        
        total_atoms = sum(atoms.values())
        if total_atoms == 0:
            descriptors.append({
                'mean_atomic_radius': np.nan,
                'electronegativity_std': np.nan,
                'cation_size_variance': np.nan,
                'valence_electron_concentration': np.nan
            })
            continue
        
        # Properties lists
        radii = []
        electronegativities = []
        cation_radii = []
        total_valence = 0.0
        
        for elem, count in atoms.items():
            r = _get_property_safe(elem, 'radius')
            en = _get_property_safe(elem, 'electronegativity')
            v = _get_property_safe(elem, 'valence')
            
            radii.append(r)
            electronegativities.append(en)
            total_valence += v * count
            
            # Determine if cation (simplified: not O, N, C, F, S, Cl, P)
            # A robust way is to check if it's in the anion list, else cation
            anions = {'O', 'N', 'C', 'F', 'S', 'Cl', 'P'}
            if elem not in anions:
                cation_radii.append(r)
        
        # 1. Mean Atomic Radius (Weighted by count)
        # Formula: Sum(r_i * n_i) / Sum(n_i)
        mean_radius = sum(r * count for r, count in zip(radii, atoms.values())) / total_atoms
        
        # 2. Electronegativity Standard Deviation (Weighted)
        # Formula: sqrt( Sum( (en_i - mean_en)^2 * n_i ) / Sum(n_i) )
        mean_en = sum(en * count for en, count in zip(electronegativities, atoms.values())) / total_atoms
        variance_en = sum(((en - mean_en) ** 2) * count for en, count in zip(electronegativities, atoms.values())) / total_atoms
        std_en = np.sqrt(variance_en)
        
        # 3. Cation Size Variance
        # Formula: Variance of cation radii
        cation_var = np.nan
        if len(cation_radii) > 1:
            # Using sample variance or population variance? Usually population for descriptors
            cation_var = np.var(cation_radii, ddof=0)
        elif len(cation_radii) == 1:
            cation_var = 0.0
        
        # 4. Valence Electron Concentration (VEC)
        # Formula: Sum(valence_electrons) / Total_atoms
        vec = total_valence / total_atoms
        
        descriptors.append({
            'mean_atomic_radius': mean_radius,
            'electronegativity_std': std_en,
            'cation_size_variance': cation_var,
            'valence_electron_concentration': vec
        })
    
    desc_df = pd.DataFrame(descriptors)
    result = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    
    logger.info(f"Descriptor computation complete. Added {len(desc_df.columns)} columns.")
    return result

# Wrapper for ingestion.py compatibility if needed, though compute_descriptors is the main entry
def main():
    """
    Main entry point for testing descriptor computation independently.
    Loads a sample dataset (if available) or runs on a mock dataframe.
    """
    logger.info("Running descriptors module main() for self-test.")
    # This is a self-test block. In the real pipeline, ingestion.py calls compute_descriptors directly.
    # We will not execute file I/O here to avoid side effects during import, 
    # but the function is designed to be called by ingestion.py.
    pass

if __name__ == "__main__":
    main()