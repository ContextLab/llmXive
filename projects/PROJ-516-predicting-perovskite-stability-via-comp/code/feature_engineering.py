"""
Feature Engineering for Perovskite Stability Prediction.

This module computes compositional descriptors including atomic fractions,
weighted averages (ionic radius, electronegativity, formation enthalpy,
first ionization energy), and variance metrics.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element
from pymatgen.core.periodic_table import get_el_symbol

# Import existing utilities
from utils.formula_parser import parse_formula, assign_perovskite_sites

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants for element properties (fallbacks if not in PeriodicTable)
# These are standard values used in materials science
IONIC_RADIUS_6COORD = {
    'Li': 0.76, 'Na': 1.02, 'K': 1.38, 'Rb': 1.52, 'Cs': 1.67,
    'Mg': 0.72, 'Ca': 1.00, 'Sr': 1.18, 'Ba': 1.35,
    'Ti': 0.605, 'Zr': 0.72, 'Hf': 0.71, 'V': 0.54, 'Nb': 0.64, 'Ta': 0.64,
    'Cr': 0.615, 'Mo': 0.69, 'W': 0.62, 'Mn': 0.645, 'Fe': 0.645, 'Co': 0.61, 'Ni': 0.60,
    'Cu': 0.73, 'Zn': 0.74, 'Ga': 0.62, 'Ge': 0.53, 'As': 0.58, 'Se': 0.50, 'Br': 0.47,
    'Sn': 0.69, 'Pb': 0.77, 'Sb': 0.60, 'Bi': 0.76, 'I': 0.39,
    'Ag': 1.15, 'In': 0.80, 'Tl': 0.885, 'Au': 1.37,
    'C': 0.16, 'N': 0.13, 'O': 1.40, 'F': 1.33,
    'H': 0.37, 'B': 0.27
}

ELECTRONEGATIVITY = {
    'H': 2.20, 'He': 0.0, 'Li': 0.98, 'Be': 1.57, 'B': 2.04, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98,
    'Na': 0.93, 'Mg': 1.31, 'Al': 1.61, 'Si': 1.90, 'P': 2.19, 'S': 2.58, 'Cl': 3.16, 'Ar': 0.0,
    'K': 0.82, 'Ca': 1.00, 'Sc': 1.36, 'Ti': 1.54, 'V': 1.63, 'Cr': 1.66, 'Mn': 1.55, 'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91, 'Cu': 1.90, 'Zn': 1.65,
    'Ga': 1.81, 'Ge': 2.01, 'As': 2.18, 'Se': 2.55, 'Br': 2.96, 'Kr': 0.0,
    'Rb': 0.82, 'Sr': 0.95, 'Y': 1.22, 'Zr': 1.33, 'Nb': 1.60, 'Mo': 2.16, 'Tc': 1.90, 'Ru': 2.20, 'Rh': 2.28, 'Pd': 2.20, 'Ag': 1.93, 'Cd': 1.69,
    'In': 1.78, 'Sn': 1.96, 'Sb': 2.05, 'Te': 2.10, 'I': 2.66, 'Xe': 0.0,
    'Cs': 0.79, 'Ba': 0.89, 'La': 1.10, 'Ce': 1.12, 'Pr': 1.13, 'Nd': 1.14, 'Pm': 1.13, 'Sm': 1.17, 'Eu': 1.20, 'Gd': 1.20, 'Tb': 1.24, 'Dy': 1.22, 'Ho': 1.23, 'Er': 1.24, 'Tm': 1.25, 'Yb': 1.10, 'Lu': 1.27,
    'Hf': 1.30, 'Ta': 1.50, 'W': 2.36, 'Re': 1.90, 'Os': 2.20, 'Ir': 2.20, 'Pt': 2.28, 'Au': 2.54, 'Hg': 2.00,
    'Tl': 1.62, 'Pb': 2.33, 'Bi': 2.02, 'Po': 2.00, 'At': 2.20, 'Rn': 0.0,
    'Fr': 0.70, 'Ra': 0.90, 'Ac': 1.10, 'Th': 1.30, 'Pa': 1.50, 'U': 1.38, 'Np': 1.36, 'Pu': 1.28, 'Am': 1.30, 'Cm': 1.30, 'Bk': 1.30, 'Cf': 1.30, 'Es': 1.30, 'Fm': 1.30, 'Md': 1.30, 'No': 1.30, 'Lr': 1.30
}

FORMATION_ENTHALPY = {
    'H': 0.0, 'He': 0.0, 'Li': 0.0, 'Be': 0.0, 'B': 0.0, 'C': 0.0, 'N': 0.0, 'O': 0.0, 'F': 0.0,
    'Na': 0.0, 'Mg': 0.0, 'Al': 0.0, 'Si': 0.0, 'P': 0.0, 'S': 0.0, 'Cl': 0.0, 'Ar': 0.0,
    'K': 0.0, 'Ca': 0.0, 'Sc': 0.0, 'Ti': 0.0, 'V': 0.0, 'Cr': 0.0, 'Mn': 0.0, 'Fe': 0.0, 'Co': 0.0, 'Ni': 0.0, 'Cu': 0.0, 'Zn': 0.0,
    'Ga': 0.0, 'Ge': 0.0, 'As': 0.0, 'Se': 0.0, 'Br': 0.0, 'Kr': 0.0,
    'Rb': 0.0, 'Sr': 0.0, 'Y': 0.0, 'Zr': 0.0, 'Nb': 0.0, 'Mo': 0.0, 'Tc': 0.0, 'Ru': 0.0, 'Rh': 0.0, 'Pd': 0.0, 'Ag': 0.0, 'Cd': 0.0,
    'In': 0.0, 'Sn': 0.0, 'Sb': 0.0, 'Te': 0.0, 'I': 0.0, 'Xe': 0.0,
    'Cs': 0.0, 'Ba': 0.0, 'La': 0.0, 'Ce': 0.0, 'Pr': 0.0, 'Nd': 0.0, 'Pm': 0.0, 'Sm': 0.0, 'Eu': 0.0, 'Gd': 0.0, 'Tb': 0.0, 'Dy': 0.0, 'Ho': 0.0, 'Er': 0.0, 'Tm': 0.0, 'Yb': 0.0, 'Lu': 0.0,
    'Hf': 0.0, 'Ta': 0.0, 'W': 0.0, 'Re': 0.0, 'Os': 0.0, 'Ir': 0.0, 'Pt': 0.0, 'Au': 0.0, 'Hg': 0.0,
    'Tl': 0.0, 'Pb': 0.0, 'Bi': 0.0, 'Po': 0.0, 'At': 0.0, 'Rn': 0.0,
    'Fr': 0.0, 'Ra': 0.0, 'Ac': 0.0, 'Th': 0.0, 'Pa': 0.0, 'U': 0.0, 'Np': 0.0, 'Pu': 0.0, 'Am': 0.0, 'Cm': 0.0, 'Bk': 0.0, 'Cf': 0.0, 'Es': 0.0, 'Fm': 0.0, 'Md': 0.0, 'No': 0.0, 'Lr': 0.0
}

FIRST_IONIZATION_ENERGY = {
    'H': 1312.0, 'He': 2372.3, 'Li': 520.2, 'Be': 899.5, 'B': 800.6, 'C': 1086.5, 'N': 1402.3, 'O': 1313.9, 'F': 1681.0,
    'Na': 495.8, 'Mg': 737.7, 'Al': 577.5, 'Si': 786.5, 'P': 1011.8, 'S': 999.6, 'Cl': 1251.2, 'Ar': 1520.6,
    'K': 418.8, 'Ca': 589.8, 'Sc': 633.1, 'Ti': 658.8, 'V': 650.9, 'Cr': 652.9, 'Mn': 717.3, 'Fe': 762.5, 'Co': 760.4, 'Ni': 737.1, 'Cu': 745.5, 'Zn': 906.4,
    'Ga': 578.8, 'Ge': 762.0, 'As': 947.0, 'Se': 941.0, 'Br': 1139.9, 'Kr': 1350.8,
    'Rb': 403.0, 'Sr': 549.5, 'Y': 616.0, 'Zr': 640.1, 'Nb': 652.1, 'Mo': 684.3, 'Tc': 702.0, 'Ru': 710.2, 'Rh': 719.7, 'Pd': 804.4, 'Ag': 731.0, 'Cd': 867.8,
    'In': 558.3, 'Sn': 708.6, 'Sb': 834.0, 'Te': 869.3, 'I': 1008.4, 'Xe': 1170.4,
    'Cs': 375.7, 'Ba': 502.9, 'La': 538.1, 'Ce': 534.4, 'Pr': 527.0, 'Nd': 533.1, 'Pm': 540.0, 'Sm': 544.5, 'Eu': 547.1, 'Gd': 593.4, 'Tb': 565.8, 'Dy': 573.0, 'Ho': 581.0, 'Er': 589.3, 'Tm': 596.7, 'Yb': 603.4, 'Lu': 523.5,
    'Hf': 658.5, 'Ta': 761.0, 'W': 770.0, 'Re': 760.0, 'Os': 840.0, 'Ir': 880.0, 'Pt': 870.0, 'Au': 890.0, 'Hg': 1007.0,
    'Tl': 589.4, 'Pb': 715.6, 'Bi': 703.0, 'Po': 812.0, 'At': 890.0, 'Rn': 1037.0,
    'Fr': 380.0, 'Ra': 509.3, 'Ac': 499.0, 'Th': 587.0, 'Pa': 568.0, 'U': 597.6, 'Np': 604.5, 'Pu': 584.7, 'Am': 578.0, 'Cm': 581.0, 'Bk': 601.0, 'Cf': 608.0, 'Es': 619.0, 'Fm': 627.0, 'Md': 635.0, 'No': 640.0, 'Lr': 470.0
}


def get_element_property(symbol: str, property_name: str) -> Optional[float]:
    """
    Retrieve a property value for a given element symbol.

    Args:
        symbol: Element symbol (e.g., 'Pb', 'I').
        property_name: One of 'ionic_radius', 'electronegativity',
                       'formation_enthalpy', 'first_ionization_energy'.

    Returns:
        The property value or None if not found.
    """
    symbol = symbol.upper()
    if property_name == 'ionic_radius':
        return IONIC_RADIUS_6COORD.get(symbol)
    elif property_name == 'electronegativity':
        return ELECTRONEGATIVITY.get(symbol)
    elif property_name == 'formation_enthalpy':
        return FORMATION_ENTHALPY.get(symbol)
    elif property_name == 'first_ionization_energy':
        return FIRST_IONIZATION_ENERGY.get(symbol)
    else:
        raise ValueError(f"Unknown property: {property_name}")


def compute_composition_descriptors(
    formula: str,
    property_name: str,
    site_assignments: Dict[str, List[str]]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Compute weighted average and variance for a given property across the composition.

    Args:
        formula: Chemical formula string (e.g., 'MAPbI3').
        property_name: The property to compute (e.g., 'electronegativity').
        site_assignments: Dict mapping site name ('A', 'B', 'X') to list of elements.

    Returns:
        Tuple of (weighted_average, variance). Returns (None, None) if data missing.
    """
    try:
        comp = Composition(formula)
        elements = comp.elements
        fractions = comp.fractional_composition
    except Exception as e:
        logger.warning(f"Failed to parse formula {formula}: {e}")
        return None, None

    weighted_sum = 0.0
    weighted_sq_sum = 0.0
    total_fraction = 0.0
    valid = True

    for el, frac in zip(elements, fractions):
        symbol = el.symbol
        val = get_element_property(symbol, property_name)
        if val is None:
            logger.warning(f"Missing property {property_name} for element {symbol} in {formula}")
            valid = False
            break
        weighted_sum += val * frac
        weighted_sq_sum += (val ** 2) * frac
        total_fraction += frac

    if not valid or total_fraction == 0:
        return None, None

    variance = weighted_sq_sum - (weighted_sum ** 2)
    return weighted_sum, variance


def load_raw_data() -> pd.DataFrame:
    """
    Load the merged raw dataset.

    Returns:
        DataFrame with at least 'formula' and 'source' columns.
    """
    input_path = Path("data/raw/perovskites_merged.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")

    df = pd.read_csv(input_path)
    required_cols = ['formula', 'source']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")

    return df


def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all required compositional descriptors for each row.

    Adds columns:
      - atomic_fraction_A, atomic_fraction_B, atomic_fraction_X
      - weighted_ionic_radius, weighted_ionic_radius_var
      - weighted_electronegativity, weighted_electronegativity_var
      - weighted_formation_enthalpy, weighted_formation_enthalpy_var
      - weighted_first_ionization_energy, weighted_first_ionization_energy_var

    Args:
        df: Input DataFrame with 'formula' column.

    Returns:
        DataFrame with new descriptor columns added.
    """
    logger.info(f"Starting descriptor computation for {len(df)} rows")

    # Initialize columns with None
    properties = [
        'ionic_radius',
        'electronegativity',
        'formation_enthalpy',
        'first_ionization_energy'
    ]

    for prop in properties:
        df[f'weighted_{prop}'] = np.nan
        df[f'weighted_{prop}_var'] = np.nan

    # Atomic fractions for A, B, X sites
    df['atomic_fraction_A'] = np.nan
    df['atomic_fraction_B'] = np.nan
    df['atomic_fraction_X'] = np.nan

    # Process row by row (safe for complex formula parsing)
    for idx, row in df.iterrows():
        formula = row['formula']
        if pd.isna(formula):
            continue

        try:
            # Parse formula and assign sites
            parsed = parse_formula(formula)
            sites = assign_perovskite_sites(parsed)

            # Compute atomic fractions per site
            # Sum fractions for elements in each site
            total_A = sum(sites.get('A', [])[1]) if 'A' in sites else 0
            total_B = sum(sites.get('B', [])[1]) if 'B' in sites else 0
            total_X = sum(sites.get('X', [])[1]) if 'X' in sites else 0
            total = total_A + total_B + total_X

            if total > 0:
                df.at[idx, 'atomic_fraction_A'] = total_A / total
                df.at[idx, 'atomic_fraction_B'] = total_B / total
                df.at[idx, 'atomic_fraction_X'] = total_X / total

            # Compute weighted averages and variances
            for prop in properties:
                w_avg, w_var = compute_composition_descriptors(formula, prop, sites)
                if w_avg is not None:
                    df.at[idx, f'weighted_{prop}'] = w_avg
                    df.at[idx, f'weighted_{prop}_var'] = w_var

        except Exception as e:
            logger.warning(f"Error processing formula {formula} at index {idx}: {e}")
            continue

    logger.info("Descriptor computation complete")
    return df


def save_descriptors(df: pd.DataFrame, output_path: str):
    """
    Save the processed descriptors to a CSV file.

    Args:
        df: DataFrame with computed descriptors.
        output_path: Path to output CSV.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    logger.info(f"Saved descriptors to {output_path}")


def main():
    """Main entry point for feature engineering."""
    logger.info("Running feature engineering pipeline")

    # Load raw data
    df = load_raw_data()

    # Compute descriptors
    df_descriptors = compute_descriptors(df)

    # Verify 'first ionization energy' column is present
    required_col = 'weighted_first_ionization_energy'
    if required_col not in df_descriptors.columns:
        raise RuntimeError(f"Required column '{required_col}' is missing from output!")

    # Check for non-null values
    non_null_count = df_descriptors[required_col].notna().sum()
    logger.info(f"Found {non_null_count} non-null values in '{required_col}' out of {len(df_descriptors)} rows")

    if non_null_count == 0:
        logger.warning("No non-null values found in 'weighted_first_ionization_energy'. Check input data and property mappings.")

    # Save output
    output_path = "data/processed/descriptors.csv"
    save_descriptors(df_descriptors, output_path)

    logger.info(f"Feature engineering complete. Output: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
