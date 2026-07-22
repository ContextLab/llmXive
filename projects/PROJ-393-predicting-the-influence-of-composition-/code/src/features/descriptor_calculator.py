import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from src.utils.periodic_table_loader import load_elemental_properties, get_element_property
from src.utils.logging_config import setup_logging, create_logger
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)

def parse_composition_string(composition: str) -> Dict[str, float]:
    # Re-use logic from composition_parser if available, or simple regex
    import re
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, str(composition))
    total = 0
    elements = {}
    for elem, count_str in matches:
        count = int(count_str) if count_str else 1
        elements[elem] = count
        total += count
    return {e: c/total for e, c in elements.items()}

def calculate_average_electronegativity(composition: Dict[str, float]) -> float:
    total = 0.0
    for elem, frac in composition.items():
        val = get_element_property(elem, 'electronegativity')
        if val is not None:
            total += val * frac
    return total

def calculate_valence_electron_concentration(composition: Dict[str, float]) -> float:
    total = 0.0
    for elem, frac in composition.items():
        val = get_element_property(elem, 'valence_electrons')
        if val is not None:
            total += val * frac
    return total

def calculate_atomic_radii_variance(composition: Dict[str, float]) -> float:
    radii = []
    weights = []
    for elem, frac in composition.items():
        val = get_element_property(elem, 'atomic_radii')
        if val is not None:
            radii.append(val)
            weights.append(frac)
    
    if not radii:
        return 0.0
    
    mean_radius = np.average(radii, weights=weights)
    variance = np.average((np.array(radii) - mean_radius)**2, weights=weights)
    return variance

def calculate_average_d_electrons(composition: Dict[str, float]) -> float:
    # Approximation: valence - s/p electrons (simplified)
    # For this task, we use valence_electrons as a proxy or specific d-electron count if available
    # Since periodic table only has valence, we use that
    return calculate_valence_electron_concentration(composition)

def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    # Same as variance
    return calculate_atomic_radii_variance(composition)

def compute_descriptors_row(row: pd.Series) -> Dict[str, float]:
    """Compute all descriptors for a single row."""
    # Extract composition string or fractions
    if 'composition' in row.index:
        comp_str = row['composition']
        if pd.isna(comp_str):
            return {}
        comp = parse_composition_string(str(comp_str))
    else:
        # Assume fraction columns exist
        comp = {}
        for col in row.index:
            if col.endswith('_frac'):
                elem = col.replace('_frac', '')
                comp[elem] = row[col]
    
    if not comp:
        return {}
    
    return {
        'avg_electronegativity': calculate_average_electronegativity(comp),
        'vec': calculate_valence_electron_concentration(comp),
        'atomic_radii_variance': calculate_atomic_radii_variance(comp),
        'avg_d_electrons': calculate_average_d_electrons(comp),
        'atomic_size_mismatch': calculate_atomic_size_mismatch(comp)
    }

def calculate_all_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate descriptors for the whole dataframe."""
    if df.empty:
        return pd.DataFrame()
    
    descriptors = df.apply(compute_descriptors_row, axis=1)
    # Convert list of dicts to DataFrame
    desc_df = pd.DataFrame(descriptors.tolist())
    return desc_df

def calculate_all_descriptors_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    return calculate_all_descriptors(df)

def main():
    setup_logging()
    logger.info("Descriptor Calculator Main Entry")
    return 0

if __name__ == "__main__":
    sys.exit(main())