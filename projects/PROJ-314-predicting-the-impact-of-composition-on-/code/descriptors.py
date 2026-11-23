"""
Descriptor Computation Module.

Computes elemental and structural descriptors from chemical compositions.
"""
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from collections import defaultdict
from chemparse import parse_formula

# Add project root to path
import os
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import periodictable
except ImportError:
    # Fallback if periodictable is not installed
    logging.warning("periodictable not found. Using mock data for descriptors.")
    periodictable = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'descriptors.log')
    ]
)
logger = logging.getLogger(__name__)

def get_element_property(element: str, property_name: str) -> Optional[float]:
    """
    Get a property of an element from the periodic table.

    Args:
        element: Element symbol (e.g., 'Al')
        property_name: Property name (e.g., 'radius', 'electronegativity')

    Returns:
        Property value or None if not found
    """
    if periodictable is None:
        # Mock values for testing
        mock_data = {
            'Al': {'radius': 1.43, 'electronegativity': 1.61, 'valence': 3},
            'O': {'radius': 0.66, 'electronegativity': 3.44, 'valence': 2},
            'Zr': {'radius': 1.60, 'electronegativity': 1.33, 'valence': 4},
            'Si': {'radius': 1.17, 'electronegativity': 1.90, 'valence': 4},
            'C': {'radius': 0.77, 'electronegativity': 2.55, 'valence': 4},
            'N': {'radius': 0.75, 'electronegativity': 3.04, 'valence': 3},
            'Mg': {'radius': 1.60, 'electronegativity': 1.31, 'valence': 2},
            'Ti': {'radius': 1.47, 'electronegativity': 1.54, 'valence': 4},
            'Hf': {'radius': 1.59, 'electronegativity': 1.30, 'valence': 4},
            'B': {'radius': 0.85, 'electronegativity': 2.04, 'valence': 3},
            'W': {'radius': 1.39, 'electronegativity': 2.36, 'valence': 6},
        }
        return mock_data.get(element, {}).get(property_name)

    try:
        elem = getattr(periodictable.elements, element)
        if property_name == 'radius':
            return elem.radius
        elif property_name == 'electronegativity':
            return elem.electronegativity
        elif property_name == 'valence':
            return elem.charge
        else:
            return getattr(elem, property_name, None)
    except Exception as e:
        logger.warning(f"Failed to get {property_name} for {element}: {e}")
        return None

def compute_valence_electron_concentration(composition: str) -> Optional[float]:
    """
    Compute Valence Electron Concentration (VEC).

    VEC = Total valence electrons / Total number of atoms

    Args:
        composition: Chemical formula

    Returns:
        VEC value or None
    """
    try:
        parsed = parse_formula(composition)
        total_valence = 0
        total_atoms = 0

        for elem, count in parsed.items():
            valence = get_element_property(elem, 'valence')
            if valence is None:
                return None
            total_valence += valence * count
            total_atoms += count

        return total_valence / total_atoms if total_atoms > 0 else None
    except Exception as e:
        logger.warning(f"Failed to compute VEC for {composition}: {e}")
        return None

def compute_mean_atomic_radius(composition: str) -> Optional[float]:
    """
    Compute mean atomic radius from stoichiometry.

    Args:
        composition: Chemical formula

    Returns:
        Mean radius or None
    """
    try:
        parsed = parse_formula(composition)
        total_radius = 0
        total_atoms = 0

        for elem, count in parsed.items():
            radius = get_element_property(elem, 'radius')
            if radius is None:
                return None
            total_radius += radius * count
            total_atoms += count

        return total_radius / total_atoms if total_atoms > 0 else None
    except Exception as e:
        logger.warning(f"Failed to compute mean radius for {composition}: {e}")
        return None

def compute_electronegativity_std(composition: str) -> Optional[float]:
    """
    Compute standard deviation of electronegativity from stoichiometry.

    Args:
        composition: Chemical formula

    Returns:
        Electronegativity std or None
    """
    try:
        parsed = parse_formula(composition)
        electronegativities = []

        for elem, count in parsed.items():
            en = get_element_property(elem, 'electronegativity')
            if en is None:
                return None
            electronegativities.extend([en] * count)

        if not electronegativities:
            return None

        return np.std(electronegativities)
    except Exception as e:
        logger.warning(f"Failed to compute EN std for {composition}: {e}")
        return None

def compute_cation_size_variance(composition: str) -> Optional[float]:
    """
    Compute variance of cation atomic radii.

    Args:
        composition: Chemical formula

    Returns:
        Cation size variance or None
    """
    try:
        parsed = parse_formula(composition)
        cation_radii = []

        # Heuristic: First element is cation
        # A more robust approach would use oxidation states
        if len(parsed) >= 2:
            cation = list(parsed.keys())[0]
            count = parsed[cation]
            radius = get_element_property(cation, 'radius')
            if radius is None:
                return None
            cation_radii.extend([radius] * count)

        if len(cation_radii) < 2:
            return 0.0  # Variance of single value is 0

        return np.var(cation_radii)
    except Exception as e:
        logger.warning(f"Failed to compute cation size variance for {composition}: {e}")
        return None

def compute_range_uncertainty(range_str: str) -> Optional[float]:
    """
    Compute range uncertainty based on extracted midpoint.

    Args:
        range_str: String representation of range (e.g., "5.0-7.0")

    Returns:
        Uncertainty value (half-width) or None
    """
    try:
        if not isinstance(range_str, str) or '-' not in range_str:
            return 0.0

        parts = range_str.split('-')
        if len(parts) != 2:
            return 0.0

        low = float(parts[0])
        high = float(parts[1])
        return (high - low) / 2.0
    except Exception as e:
        logger.warning(f"Failed to compute range uncertainty for {range_str}: {e}")
        return None

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all descriptors for a DataFrame of compositions.

    Args:
        df: DataFrame with 'composition' column

    Returns:
        DataFrame with added descriptor columns
    """
    logger.info(f"Computing descriptors for {len(df)} entries...")

    df['mean_atomic_radius'] = df['composition'].apply(compute_mean_atomic_radius)
    df['electronegativity_std'] = df['composition'].apply(compute_electronegativity_std)
    df['valence_electron_concentration'] = df['composition'].apply(compute_valence_electron_concentration)
    df['cation_size_variance'] = df['composition'].apply(compute_cation_size_variance)

    # Handle range uncertainty if 'range_original' exists
    if 'range_original' in df.columns:
        df['range_uncertainty'] = df['range_original'].apply(compute_range_uncertainty)

    logger.info("Descriptor computation completed.")
    return df

def main():
    """Main entry point for descriptor computation."""
    logger.info("Descriptor computation module loaded.")

if __name__ == "__main__":
    main()
