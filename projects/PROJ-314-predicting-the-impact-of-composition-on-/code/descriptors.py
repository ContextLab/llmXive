import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from chemparse import Composition
import numpy as np
from collections import defaultdict
import os
import sys

# Import configuration utilities
try:
    from config import get_config_value, get_float_config
except ImportError:
    # Fallback for direct execution or different import context
    import os
    def get_config_value(key, default=None):
        return os.getenv(key, default)
    def get_float_config(key, default=None):
        val = os.getenv(key, default)
        return float(val) if val is not None else default

logger = logging.getLogger(__name__)

# Periodic table data for atomic properties
# Source: Standard IUPAC values (approximate for common oxidation states where necessary)
ATOMIC_PROPERTIES = {
    'H': {'radius': 37.0, 'electronegativity': 2.20, 'valence_electrons': 1},
    'He': {'radius': 32.0, 'electronegativity': None, 'valence_electrons': 0}, # Noble gas, often 0 valence in compounds
    'Li': {'radius': 152.0, 'electronegativity': 0.98, 'valence_electrons': 1},
    'Be': {'radius': 112.0, 'electronegativity': 1.57, 'valence_electrons': 2},
    'B': {'radius': 85.0, 'electronegativity': 2.04, 'valence_electrons': 3},
    'C': {'radius': 77.0, 'electronegativity': 2.55, 'valence_electrons': 4},
    'N': {'radius': 75.0, 'electronegativity': 3.04, 'valence_electrons': 5},
    'O': {'radius': 73.0, 'electronegativity': 3.44, 'valence_electrons': 6},
    'F': {'radius': 72.0, 'electronegativity': 3.98, 'valence_electrons': 7},
    'Ne': {'radius': 71.0, 'electronegativity': None, 'valence_electrons': 0},
    'Na': {'radius': 186.0, 'electronegativity': 0.93, 'valence_electrons': 1},
    'Mg': {'radius': 160.0, 'electronegativity': 1.31, 'valence_electrons': 2},
    'Al': {'radius': 143.0, 'electronegativity': 1.61, 'valence_electrons': 3},
    'Si': {'radius': 117.0, 'electronegativity': 1.90, 'valence_electrons': 4},
    'P': {'radius': 110.0, 'electronegativity': 2.19, 'valence_electrons': 5},
    'S': {'radius': 104.0, 'electronegativity': 2.58, 'valence_electrons': 6},
    'Cl': {'radius': 99.0, 'electronegativity': 3.16, 'valence_electrons': 7},
    'Ar': {'radius': 98.0, 'electronegativity': None, 'valence_electrons': 0},
    'K': {'radius': 227.0, 'electronegativity': 0.82, 'valence_electrons': 1},
    'Ca': {'radius': 197.0, 'electronegativity': 1.00, 'valence_electrons': 2},
    'Sc': {'radius': 162.0, 'electronegativity': 1.36, 'valence_electrons': 3},
    'Ti': {'radius': 147.0, 'electronegativity': 1.54, 'valence_electrons': 4},
    'V': {'radius': 134.0, 'electronegativity': 1.63, 'valence_electrons': 5},
    'Cr': {'radius': 128.0, 'electronegativity': 1.66, 'valence_electrons': 6},
    'Mn': {'radius': 127.0, 'electronegativity': 1.55, 'valence_electrons': 7},
    'Fe': {'radius': 126.0, 'electronegativity': 1.83, 'valence_electrons': 8}, # Commonly 2 or 3, but group valence is 8
    'Co': {'radius': 125.0, 'electronegativity': 1.88, 'valence_electrons': 9},
    'Ni': {'radius': 124.0, 'electronegativity': 1.91, 'valence_electrons': 10},
    'Cu': {'radius': 128.0, 'electronegativity': 1.90, 'valence_electrons': 11},
    'Zn': {'radius': 134.0, 'electronegativity': 1.65, 'valence_electrons': 12},
    'Ga': {'radius': 135.0, 'electronegativity': 1.81, 'valence_electrons': 3},
    'Ge': {'radius': 122.0, 'electronegativity': 2.01, 'valence_electrons': 4},
    'As': {'radius': 121.0, 'electronegativity': 2.18, 'valence_electrons': 5},
    'Se': {'radius': 117.0, 'electronegativity': 2.55, 'valence_electrons': 6},
    'Br': {'radius': 114.0, 'electronegativity': 2.96, 'valence_electrons': 7},
    'Kr': {'radius': 110.0, 'electronegativity': 3.00, 'valence_electrons': 0},
    'Rb': {'radius': 248.0, 'electronegativity': 0.82, 'valence_electrons': 1},
    'Sr': {'radius': 215.0, 'electronegativity': 0.95, 'valence_electrons': 2},
    'Y': {'radius': 180.0, 'electronegativity': 1.22, 'valence_electrons': 3},
    'Zr': {'radius': 160.0, 'electronegativity': 1.33, 'valence_electrons': 4},
    'Nb': {'radius': 146.0, 'electronegativity': 1.60, 'valence_electrons': 5},
    'Mo': {'radius': 139.0, 'electronegativity': 2.16, 'valence_electrons': 6},
    'Tc': {'radius': 136.0, 'electronegativity': 1.90, 'valence_electrons': 7},
    'Ru': {'radius': 134.0, 'electronegativity': 2.20, 'valence_electrons': 8},
    'Rh': {'radius': 134.0, 'electronegativity': 2.28, 'valence_electrons': 9},
    'Pd': {'radius': 137.0, 'electronegativity': 2.20, 'valence_electrons': 10},
    'Ag': {'radius': 144.0, 'electronegativity': 1.93, 'valence_electrons': 11},
    'Cd': {'radius': 151.0, 'electronegativity': 1.69, 'valence_electrons': 12},
    'In': {'radius': 167.0, 'electronegativity': 1.78, 'valence_electrons': 3},
    'Sn': {'radius': 140.0, 'electronegativity': 1.96, 'valence_electrons': 4},
    'Sb': {'radius': 140.0, 'electronegativity': 2.05, 'valence_electrons': 5},
    'Te': {'radius': 136.0, 'electronegativity': 2.10, 'valence_electrons': 6},
    'I': {'radius': 133.0, 'electronegativity': 2.66, 'valence_electrons': 7},
    'Xe': {'radius': 130.0, 'electronegativity': 2.60, 'valence_electrons': 0},
    'Cs': {'radius': 265.0, 'electronegativity': 0.79, 'valence_electrons': 1},
    'Ba': {'radius': 222.0, 'electronegativity': 0.89, 'valence_electrons': 2},
    'La': {'radius': 187.0, 'electronegativity': 1.10, 'valence_electrons': 3},
    'Ce': {'radius': 181.0, 'electronegativity': 1.12, 'valence_electrons': 4},
    'Pr': {'radius': 182.0, 'electronegativity': 1.13, 'valence_electrons': 3},
    'Nd': {'radius': 181.0, 'electronegativity': 1.14, 'valence_electrons': 3},
    'Pm': {'radius': 183.0, 'electronegativity': 1.13, 'valence_electrons': 3},
    'Sm': {'radius': 180.0, 'electronegativity': 1.17, 'valence_electrons': 3},
    'Eu': {'radius': 199.0, 'electronegativity': 1.20, 'valence_electrons': 3},
    'Gd': {'radius': 180.0, 'electronegativity': 1.20, 'valence_electrons': 3},
    'Tb': {'radius': 175.0, 'electronegativity': 1.20, 'valence_electrons': 3},
    'Dy': {'radius': 178.0, 'electronegativity': 1.22, 'valence_electrons': 3},
    'Ho': {'radius': 176.0, 'electronegativity': 1.23, 'valence_electrons': 3},
    'Er': {'radius': 176.0, 'electronegativity': 1.24, 'valence_electrons': 3},
    'Tm': {'radius': 176.0, 'electronegativity': 1.25, 'valence_electrons': 3},
    'Yb': {'radius': 194.0, 'electronegativity': 1.10, 'valence_electrons': 3},
    'Lu': {'radius': 174.0, 'electronegativity': 1.27, 'valence_electrons': 3},
    'Hf': {'radius': 159.0, 'electronegativity': 1.30, 'valence_electrons': 4},
    'Ta': {'radius': 146.0, 'electronegativity': 1.50, 'valence_electrons': 5},
    'W': {'radius': 139.0, 'electronegativity': 2.36, 'valence_electrons': 6},
    'Re': {'radius': 137.0, 'electronegativity': 1.90, 'valence_electrons': 7},
    'Os': {'radius': 135.0, 'electronegativity': 2.20, 'valence_electrons': 8},
    'Ir': {'radius': 136.0, 'electronegativity': 2.20, 'valence_electrons': 9},
    'Pt': {'radius': 139.0, 'electronegativity': 2.28, 'valence_electrons': 10},
    'Au': {'radius': 144.0, 'electronegativity': 2.54, 'valence_electrons': 11},
    'Hg': {'radius': 151.0, 'electronegativity': 2.00, 'valence_electrons': 12},
    'Tl': {'radius': 170.0, 'electronegativity': 2.04, 'valence_electrons': 3},
    'Pb': {'radius': 147.0, 'electronegativity': 2.33, 'valence_electrons': 4},
    'Bi': {'radius': 146.0, 'electronegativity': 2.02, 'valence_electrons': 5},
    'Po': {'radius': 140.0, 'electronegativity': 2.00, 'valence_electrons': 6},
    'At': {'radius': 140.0, 'electronegativity': 2.20, 'valence_electrons': 7},
    'Rn': {'radius': 140.0, 'electronegativity': 2.20, 'valence_electrons': 0},
}

def get_valence_electrons(element: str) -> Optional[int]:
    """
    Retrieve the number of valence electrons for a given element.
    Returns None if the element is not found or is a noble gas (often 0 in this context).
    """
    element = element.upper()
    if element in ATOMIC_PROPERTIES:
        return ATOMIC_PROPERTIES[element].get('valence_electrons')
    logger.warning(f"Valence electrons not found for element: {element}")
    return None

def compute_valence_electron_concentration(composition_str: str) -> Optional[float]:
    """
    Calculate the Valence Electron Concentration (VEC) for a given composition string.
    VEC = (Total Valence Electrons) / (Total Number of Atoms)

    Args:
        composition_str (str): Chemical composition string (e.g., 'Al2O3', 'BaTiO3').

    Returns:
        float or None: The calculated VEC, or None if calculation fails.
    """
    if not composition_str or not isinstance(composition_str, str):
        logger.error(f"Invalid composition string: {composition_str}")
        return None

    try:
        parsed = Composition(composition_str)
    except Exception as e:
        logger.error(f"Failed to parse composition '{composition_str}': {e}")
        return None

    total_valence = 0.0
    total_atoms = 0.0

    for element, count in parsed.items():
        valence = get_valence_electrons(element)
        if valence is None:
            # If we can't determine valence, we cannot compute VEC accurately
            logger.warning(f"Cannot compute VEC for {composition_str}: missing valence for {element}")
            return None

        total_valence += valence * count
        total_atoms += count

    if total_atoms == 0:
        logger.warning(f"Total atoms is zero for composition: {composition_str}")
        return None

    return total_valence / total_atoms

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all compositional descriptors for the dataset.
    Includes: mean_atomic_radius, electronegativity_std, valence_electron_concentration.

    Args:
        df (pd.DataFrame): DataFrame containing a 'composition' column.

    Returns:
        pd.DataFrame: DataFrame with new descriptor columns appended.
    """
    logger.info("Computing compositional descriptors...")

    # Apply VEC calculation
    df['valence_electron_concentration'] = df['composition'].apply(compute_valence_electron_concentration)

    # Note: mean_atomic_radius and electronegativity_std are implemented in T019a and T019b.
    # This function ensures VEC is computed and added to the dataframe.
    # If other descriptors are missing in the dataframe, they should be handled by their respective functions
    # or a combined pipeline, but for T019c, we focus on VEC.

    return df

def main():
    """
    Main entry point for descriptor computation if run as a script.
    Expects a CSV file path as an argument or uses a default path.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compute compositional descriptors.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV file")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        df = pd.read_csv(args.input)
        if 'composition' not in df.columns:
            raise ValueError("Input CSV must contain a 'composition' column.")

        df = compute_descriptors(df)
        df.to_csv(args.output, index=False)
        logger.info(f"Descriptors computed and saved to {args.output}")
    except Exception as e:
        logger.error(f"Error in descriptor computation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()