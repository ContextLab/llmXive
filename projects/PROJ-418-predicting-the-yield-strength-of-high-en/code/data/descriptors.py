import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from utils.logging import get_logger

logger = get_logger(__name__)

# Elemental properties database (simplified for common HEA elements)
# Source: Standard literature values (Atomic radius in pm, Electronegativity Pauling, Valence e-)
ELEMENTAL_PROPERTIES = {
    'Cr': {'radius': 128, 'electronegativity': 1.66, 'valence': 6},
    'Co': {'radius': 125, 'electronegativity': 1.88, 'valence': 9},
    'Fe': {'radius': 126, 'electronegativity': 1.83, 'valence': 8},
    'Ni': {'radius': 124, 'electronegativity': 1.91, 'valence': 10},
    'Mn': {'radius': 127, 'electronegativity': 1.55, 'valence': 7},
    'Al': {'radius': 143, 'electronegativity': 1.61, 'valence': 3},
    'Cu': {'radius': 128, 'electronegativity': 1.90, 'valence': 11},
    'Ti': {'radius': 147, 'electronegativity': 1.54, 'valence': 4},
    'V': {'radius': 134, 'electronegativity': 1.63, 'valence': 5},
    'Nb': {'radius': 146, 'electronegativity': 1.60, 'valence': 5},
    'Ta': {'radius': 146, 'electronegativity': 1.50, 'valence': 5},
    'Mo': {'radius': 139, 'electronegativity': 2.16, 'valence': 6},
    'W': {'radius': 139, 'electronegativity': 2.36, 'valence': 6},
    'Zr': {'radius': 160, 'electronegativity': 1.33, 'valence': 4},
    'Hf': {'radius': 159, 'electronegativity': 1.30, 'valence': 4},
    'Si': {'radius': 117, 'electronegativity': 1.90, 'valence': 4},
    'C':  {'radius': 77,  'electronegativity': 2.55, 'valence': 4},
    'O':  {'radius': 73,  'electronegativity': 3.44, 'valence': 6},
}

def get_elemental_properties() -> Dict[str, Dict[str, float]]:
    """Returns the dictionary of elemental properties."""
    return ELEMENTAL_PROPERTIES

def get_property(element: str, property_name: str) -> Optional[float]:
    """
    Retrieves a specific property for an element.
    
    Args:
        element: Element symbol (e.g., 'Fe')
        property_name: Property key ('radius', 'electronegativity', 'valence')
    
    Returns:
        The property value or None if not found.
    """
    if element not in ELEMENTAL_PROPERTIES:
        logger.warning(f"Element {element} not found in database.")
        return None
    return ELEMENTAL_PROPERTIES[element].get(property_name)

def calculate_weighted_average(values: List[float], fractions: List[float]) -> float:
    """Calculates the weighted average of a list of values."""
    if not values or not fractions:
        return 0.0
    if len(values) != len(fractions):
        raise ValueError("Values and fractions must have the same length.")
    return sum(v * f for v, f in zip(values, fractions))

def calculate_single_composition_descriptors(row: pd.Series, props: Dict[str, Dict]) -> Dict[str, float]:
    """
    Calculates descriptors for a single row (composition).
    Expected columns: Element1, Elem_Frac1, Element2, Elem_Frac2, ... (up to N elements)
    Or a dictionary format if the CSV is structured differently.
    This function assumes a wide format where elements and fractions are paired.
    """
    # Identify element and fraction columns
    element_cols = [c for c in row.index if c.startswith('Element')]
    fraction_cols = [c for c in row.index if c.startswith('Elem_Frac') or c.startswith('Fraction')]
    
    # If no specific element columns found, try to detect all element columns (e.g., Cr, Fe, Ni)
    # This is a heuristic: if columns look like element symbols
    if not element_cols:
        # Check for columns that are known element symbols
        known_elements = set(props.keys())
        element_cols = [c for c in row.index if c in known_elements]
        # Fractions should be the same columns? Or separate? 
        # Assuming the row has the fraction directly for the element column if wide format
        # e.g. Cr: 0.2, Fe: 0.2...
        if element_cols:
            fractions = [row[c] for c in element_cols]
            elements = element_cols
        else:
            # Fallback: try to find columns with 'Cr', 'Fe' etc in name? Too risky.
            # Assume standard format: Element1, Elem_Frac1...
            logger.error("Could not identify element columns in row.")
            return {}
    else:
        # Standard wide format: Element1, Elem_Frac1, Element2, Elem_Frac2
        elements = []
        fractions = []
        for ec, fc in zip(element_cols, fraction_cols):
            # Ensure they are paired correctly by index
            # This assumes Element1 pairs with Elem_Frac1
            pass
        # Sort by index to ensure pairing
        combined = sorted(zip(element_cols, fraction_cols), key=lambda x: int(x[0].replace('Element', '').replace('Elem_Frac', '')))
        elements = [c[0] for c in combined]
        fractions = [row[c[1]] for c in combined]

    if not elements or not fractions:
        return {}

    # Normalize fractions to sum to 1 (handle missing/NaN)
    valid_fractions = [f for f in fractions if pd.notna(f)]
    valid_elements = [e for e, f in zip(elements, fractions) if pd.notna(f)]
    
    if not valid_fractions:
        return {}
        
    total_frac = sum(valid_fractions)
    if total_frac == 0:
        return {}
    fractions = [f/total_frac for f in valid_fractions]
    elements = valid_elements

    # Extract properties
    radii = []
    electronegativities = []
    valences = []
    melting_temps = [] # Placeholder, need Tm data if available

    for elem in elements:
        r = get_property(elem, 'radius')
        chi = get_property(elem, 'electronegativity')
        v = get_property(elem, 'valence')
        # Tm not in our simple DB, setting to 0 or skipping if needed
        # For now, assume Tm is not calculated if not in DB
        
        if r is None or chi is None or v is None:
            logger.warning(f"Missing properties for {elem}.")
            return {} # Skip this row if missing any property
        
        radii.append(r)
        electronegativities.append(chi)
        valences.append(v)
        melting_temps.append(0) # Placeholder

    # 1. Atomic Size Difference (delta)
    # delta = sqrt( sum( c_i * (1 - r_i/r_avg)^2 ) )
    r_avg = calculate_weighted_average(radii, fractions)
    delta_sq = sum(f * (1 - r/r_avg)**2 for r, f in zip(radii, fractions))
    delta = 100 * np.sqrt(delta_sq) # Often expressed as percentage

    # 2. Electronegativity Difference (Delta Chi)
    chi_avg = calculate_weighted_average(electronegativities, fractions)
    delta_chi = np.sqrt(sum(f * (chi - chi_avg)**2 for chi, f in zip(electronegativities, fractions)))

    # 3. Valence Electron Concentration (VEC)
    vec = calculate_weighted_average(valences, fractions)

    # 4. Mixing Entropy (Delta S_mix)
    # -R * sum(c_i * ln(c_i))
    # R = 8.314 J/(mol K)
    # c_i must be > 0
    s_mix = 0.0
    for c in fractions:
        if c > 0:
            s_mix += c * np.log(c)
    s_mix = -8.314 * s_mix

    # 5. Melting Temperature Variance (Delta Tm)
    # If we had Tm data: sqrt( sum(c_i * (Tm_i - Tm_avg)^2) )
    # Since we don't have Tm in DB, we return 0 or skip.
    # For this implementation, we assume 0 or return None if Tm required.
    delta_tm = 0.0 

    return {
        'delta': delta,
        'delta_chi': delta_chi,
        'VEC': vec,
        'S_mix': s_mix,
        'delta_Tm': delta_tm
    }

def calculate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies calculate_single_composition_descriptors to the entire DataFrame.
    
    Args:
        df: DataFrame with elemental composition columns.
    
    Returns:
        DataFrame with appended descriptor columns.
    """
    props = get_elemental_properties()
    
    descriptors = []
    for idx, row in df.iterrows():
        desc = calculate_single_composition_descriptors(row, props)
        if desc:
            descriptors.append(desc)
        else:
            descriptors.append({
                'delta': np.nan,
                'delta_chi': np.nan,
                'VEC': np.nan,
                'S_mix': np.nan,
                'delta_Tm': np.nan
            })
    
    desc_df = pd.DataFrame(descriptors)
    
    # Concatenate
    result_df = pd.concat([df, desc_df], axis=1)
    return result_df

def filter_missing_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows where any descriptor is NaN (indicating missing elemental properties).
    
    Args:
        df: DataFrame with descriptors.
    
    Returns:
        Filtered DataFrame.
    """
    desc_cols = ['delta', 'delta_chi', 'VEC', 'S_mix', 'delta_Tm']
    # Check if these columns exist
    existing_cols = [c for c in desc_cols if c in df.columns]
    if not existing_cols:
        logger.warning("No descriptor columns found to filter.")
        return df
    
    initial_count = len(df)
    df = df.dropna(subset=existing_cols)
    logger.info(f"Filtered {initial_count - len(df)} rows with missing properties.")
    return df

def main():
    logger.info("Descriptors module loaded.")

if __name__ == "__main__":
    main()
