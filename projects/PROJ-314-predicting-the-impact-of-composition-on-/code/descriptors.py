"""
Descriptor computation module for ceramic properties.
Calculates elemental descriptors based on stoichiometry.
"""
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from collections import defaultdict
from chemparse import parse_formula
from pymatgen.core import Composition as PmgComposition
from code.config import get_config_value

logger = logging.getLogger(__name__)

# Periodic table data for electronegativity (Pauling scale)
# Source: Standard chemical data
ELECTRONEGATIVITY_DATA = {
    'H': 2.20, 'He': None,
    'Li': 0.98, 'Be': 1.57, 'B': 2.04, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98, 'Ne': None,
    'Na': 0.93, 'Mg': 1.31, 'Al': 1.61, 'Si': 1.90, 'P': 2.19, 'S': 2.58, 'Cl': 3.16, 'Ar': None,
    'K': 0.82, 'Ca': 1.00, 'Sc': 1.36, 'Ti': 1.54, 'V': 1.63, 'Cr': 1.66, 'Mn': 1.55, 'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91, 'Cu': 1.90, 'Zn': 1.65, 'Ga': 1.81, 'Ge': 2.01, 'As': 2.18, 'Se': 2.55, 'Br': 2.96, 'Kr': 3.00,
    'Rb': 0.82, 'Sr': 0.95, 'Y': 1.22, 'Zr': 1.33, 'Nb': 1.60, 'Mo': 2.16, 'Tc': 1.90, 'Ru': 2.20, 'Rh': 2.28, 'Pd': 2.20, 'Ag': 1.93, 'Cd': 1.69, 'In': 1.78, 'Sn': 1.96, 'Sb': 2.05, 'Te': 2.10, 'I': 2.66, 'Xe': 2.60,
    'Cs': 0.79, 'Ba': 0.89, 'La': 1.10, 'Ce': 1.12, 'Pr': 1.13, 'Nd': 1.14, 'Pm': None, 'Sm': 1.17, 'Eu': None, 'Gd': 1.20, 'Tb': 1.20, 'Dy': 1.22, 'Ho': 1.23, 'Er': 1.24, 'Tm': 1.25, 'Yb': None, 'Lu': 1.27,
    'Hf': 1.30, 'Ta': 1.50, 'W': 2.36, 'Re': 1.90, 'Os': 2.20, 'Ir': 2.20, 'Pt': 2.28, 'Au': 2.54, 'Hg': 2.00, 'Tl': 1.62, 'Pb': 2.33, 'Bi': 2.02, 'Po': 2.00, 'At': 2.20, 'Rn': None,
    'Fr': 0.70, 'Ra': 0.90, 'Ac': 1.10, 'Th': 1.30, 'Pa': 1.50, 'U': 1.38, 'Np': 1.36, 'Pu': 1.28, 'Am': 1.30, 'Cm': 1.30, 'Bk': None, 'Cf': None, 'Es': None, 'Fm': None, 'Md': None, 'No': None, 'Lr': None,
    'Rf': None, 'Db': None, 'Sg': None, 'Bh': None, 'Hs': None, 'Mt': None, 'Ds': None, 'Rg': None, 'Cn': None, 'Nh': None, 'Fl': None, 'Mc': None, 'Lv': None, 'Ts': None, 'Og': None
}

def compute_mean_atomic_radius(composition_str: str) -> Optional[float]:
    """
    Calculate the mean atomic radius from a composition string.
    Uses stoichiometry-weighted average of elemental atomic radii.
    """
    try:
        parsed = parse_formula(composition_str)
        if not parsed:
            return None

        # Atomic radii (pm) - empirical values
        ATOMIC_RADIUS_DATA = {
            'H': 37, 'He': 32,
            'Li': 152, 'Be': 112, 'B': 85, 'C': 77, 'N': 75, 'O': 73, 'F': 72, 'Ne': 71,
            'Na': 186, 'Mg': 160, 'Al': 143, 'Si': 117, 'P': 110, 'S': 104, 'Cl': 99, 'Ar': 97,
            'K': 227, 'Ca': 197, 'Sc': 162, 'Ti': 147, 'V': 134, 'Cr': 128, 'Mn': 127, 'Fe': 126, 'Co': 125, 'Ni': 124, 'Cu': 128, 'Zn': 134, 'Ga': 135, 'Ge': 122, 'As': 121, 'Se': 117, 'Br': 114, 'Kr': 110,
            'Rb': 248, 'Sr': 215, 'Y': 180, 'Zr': 160, 'Nb': 146, 'Mo': 139, 'Tc': 136, 'Ru': 134, 'Rh': 134, 'Pd': 137, 'Ag': 144, 'Cd': 151, 'In': 167, 'Sn': 140, 'Sb': 140, 'Te': 136, 'I': 133, 'Xe': 130,
            'Cs': 265, 'Ba': 222, 'La': 187, 'Ce': 182, 'Pr': 182, 'Nd': 181, 'Pm': 180, 'Sm': 180, 'Eu': 199, 'Gd': 179, 'Tb': 177, 'Dy': 177, 'Ho': 176, 'Er': 176, 'Tm': 175, 'Yb': 194, 'Lu': 174,
            'Hf': 159, 'Ta': 146, 'W': 139, 'Re': 137, 'Os': 135, 'Ir': 136, 'Pt': 139, 'Au': 144, 'Hg': 151, 'Tl': 170, 'Pb': 175, 'Bi': 156, 'Po': 167, 'At': 145, 'Rn': 140
        }

        total_weight = 0.0
        weighted_sum = 0.0
        count = 0

        for element, amount in parsed.items():
            if element in ATOMIC_RADIUS_DATA:
                radius = ATOMIC_RADIUS_DATA[element]
                weighted_sum += radius * amount
                total_weight += amount
                count += 1

        if total_weight == 0:
            return None

        return weighted_sum / total_weight
    except Exception as e:
        logger.warning(f"Failed to compute mean atomic radius for {composition_str}: {e}")
        return None

def compute_electronegativity_std(composition_str: str) -> Optional[float]:
    """
    Calculate the standard deviation of electronegativity from stoichiometry.
    
    Args:
        composition_str: Chemical formula string (e.g., 'Al2O3')
        
    Returns:
        Standard deviation of electronegativity values weighted by stoichiometry,
        or None if computation fails.
    """
    try:
        parsed = parse_formula(composition_str)
        if not parsed:
            return None

        electronegativity_values = []
        weights = []

        for element, amount in parsed.items():
            if element in ELECTRONEGATIVITY_DATA:
                en_val = ELECTRONEGATIVITY_DATA[element]
                if en_val is not None:
                    # Add the value 'amount' times to the list for weighted calculation
                    # Or use weighted mean/variance formula directly
                    electronegativity_values.extend([en_val] * amount)
                    weights.extend([1] * amount)

        if len(electronegativity_values) < 2:
            return 0.0

        # Calculate weighted standard deviation
        # Using numpy for convenience
        values = np.array(electronegativity_values)
        
        # Weighted mean
        mean_en = np.average(values)
        
        # Weighted variance
        variance = np.average((values - mean_en) ** 2)
        
        std_en = np.sqrt(variance)
        
        return float(std_en)
    except Exception as e:
        logger.warning(f"Failed to compute electronegativity std for {composition_str}: {e}")
        return None

def compute_valence_electron_concentration(composition_str: str) -> Optional[float]:
    """
    Calculate the Valence Electron Concentration (VEC).
    VEC = Total valence electrons / Total number of atoms.
    
    Args:
        composition_str: Chemical formula string
        
    Returns:
        VEC value or None if computation fails.
    """
    try:
        parsed = parse_formula(composition_str)
        if not parsed:
            return None

        # Valence electrons for common elements (simplified)
        VALENCE_ELECTRONS = {
            'H': 1, 'He': 8,
            'Li': 1, 'Be': 2, 'B': 3, 'C': 4, 'N': 5, 'O': 6, 'F': 7, 'Ne': 8,
            'Na': 1, 'Mg': 2, 'Al': 3, 'Si': 4, 'P': 5, 'S': 6, 'Cl': 7, 'Ar': 8,
            'K': 1, 'Ca': 2, 'Sc': 3, 'Ti': 4, 'V': 5, 'Cr': 6, 'Mn': 7, 'Fe': 8, 'Co': 9, 'Ni': 10, 'Cu': 11, 'Zn': 12,
            'Ga': 3, 'Ge': 4, 'As': 5, 'Se': 6, 'Br': 7, 'Kr': 8,
            'Rb': 1, 'Sr': 2, 'Y': 3, 'Zr': 4, 'Nb': 5, 'Mo': 6, 'Tc': 7, 'Ru': 8, 'Rh': 9, 'Pd': 10, 'Ag': 11, 'Cd': 12,
            'In': 3, 'Sn': 4, 'Sb': 5, 'Te': 6, 'I': 7, 'Xe': 8,
            'Cs': 1, 'Ba': 2, 'La': 3, 'Ce': 4, 'Pr': 4, 'Nd': 4, 'Sm': 4, 'Eu': 3, 'Gd': 4, 'Tb': 4, 'Dy': 4, 'Ho': 4, 'Er': 4, 'Tm': 4, 'Yb': 3, 'Lu': 4,
            'Hf': 4, 'Ta': 5, 'W': 6, 'Re': 7, 'Os': 8, 'Ir': 9, 'Pt': 10, 'Au': 11, 'Hg': 12,
            'Tl': 3, 'Pb': 4, 'Bi': 5, 'Po': 6
        }

        total_valence = 0
        total_atoms = 0

        for element, amount in parsed.items():
            if element in VALENCE_ELECTRONS:
                total_valence += VALENCE_ELECTRONS[element] * amount
                total_atoms += amount

        if total_atoms == 0:
            return None

        return float(total_valence / total_atoms)
    except Exception as e:
        logger.warning(f"Failed to compute VEC for {composition_str}: {e}")
        return None

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all descriptors for a DataFrame of ceramic entries.
    
    Args:
        df: DataFrame with a 'composition' column
        
    Returns:
        DataFrame with added descriptor columns
    """
    logger.info(f"Computing descriptors for {len(df)} entries...")
    
    # Apply descriptor calculations
    df['mean_atomic_radius'] = df['composition'].apply(compute_mean_atomic_radius)
    df['electronegativity_std'] = df['composition'].apply(compute_electronegativity_std)
    df['valence_electron_concentration'] = df['composition'].apply(compute_valence_electron_concentration)
    
    # Log results
    missing_radius = df['mean_atomic_radius'].isna().sum()
    missing_en = df['electronegativity_std'].isna().sum()
    missing_vec = df['valence_electron_concentration'].isna().sum()
    
    logger.info(f"Descriptor computation complete. Missing: Radius={missing_radius}, EN_Std={missing_en}, VEC={missing_vec}")
    
    return df

def main():
    """
    Main entry point for descriptor computation.
    Loads processed data, computes descriptors, and saves the result.
    """
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Compute descriptors for ceramic data")
    parser.add_argument("--input", type=str, default="data/processed/step4_final.csv",
                      help="Input CSV file path")
    parser.add_argument("--output", type=str, default="data/processed/descriptors_computed.csv",
                      help="Output CSV file path")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Compute descriptors
    df = compute_descriptors(df)
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info("Descriptor computation completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())