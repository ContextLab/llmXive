import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from utils.logging import get_logger

logger = get_logger(__name__)

# Standard elemental properties database
# Sources: WebElements, CRC Handbook, standard materials databases
ELEMENTAL_PROPERTIES = {
    'Al': {'atomic_radius': 143.0, 'electronegativity': 1.61, 'valence_electrons': 3, 'melting_point': 933.47},
    'Cr': {'atomic_radius': 128.0, 'electronegativity': 1.66, 'valence_electrons': 6, 'melting_point': 2180.0},
    'Co': {'atomic_radius': 125.0, 'electronegativity': 1.88, 'valence_electrons': 9, 'melting_point': 1768.0},
    'Cu': {'atomic_radius': 128.0, 'electronegativity': 1.90, 'valence_electrons': 11, 'melting_point': 1357.77},
    'Fe': {'atomic_radius': 126.0, 'electronegativity': 1.83, 'valence_electrons': 8, 'melting_point': 1811.0},
    'Mn': {'atomic_radius': 127.0, 'electronegativity': 1.55, 'valence_electrons': 7, 'melting_point': 1519.0},
    'Mo': {'atomic_radius': 139.0, 'electronegativity': 2.16, 'valence_electrons': 6, 'melting_point': 2896.0},
    'Nb': {'atomic_radius': 146.0, 'electronegativity': 1.60, 'valence_electrons': 5, 'melting_point': 2750.0},
    'Ni': {'atomic_radius': 124.0, 'electronegativity': 1.91, 'valence_electrons': 10, 'melting_point': 1728.0},
    'Re': {'atomic_radius': 137.0, 'electronegativity': 1.90, 'valence_electrons': 7, 'melting_point': 3459.0},
    'Ru': {'atomic_radius': 134.0, 'electronegativity': 2.20, 'valence_electrons': 8, 'melting_point': 2607.0},
    'Si': {'atomic_radius': 111.0, 'electronegativity': 1.90, 'valence_electrons': 4, 'melting_point': 1687.0},
    'Ta': {'atomic_radius': 146.0, 'electronegativity': 1.50, 'valence_electrons': 5, 'melting_point': 3290.0},
    'Ti': {'atomic_radius': 147.0, 'electronegativity': 1.54, 'valence_electrons': 4, 'melting_point': 1941.0},
    'V': {'atomic_radius': 134.0, 'electronegativity': 1.63, 'valence_electrons': 5, 'melting_point': 2183.0},
    'W': {'atomic_radius': 139.0, 'electronegativity': 2.36, 'valence_electrons': 6, 'melting_point': 3695.0},
    'Zr': {'atomic_radius': 160.0, 'electronegativity': 1.33, 'valence_electrons': 4, 'melting_point': 2128.0},
}

def get_elemental_properties() -> Dict[str, Dict[str, float]]:
    """Return the dictionary of elemental properties."""
    return ELEMENTAL_PROPERTIES.copy()

def get_property(element: str, property_name: str) -> Optional[float]:
    """
    Get a specific property for an element.
    
    Args:
        element: Element symbol (e.g., 'Fe')
        property_name: Property name (e.g., 'atomic_radius')
        
    Returns:
        Property value if found, None otherwise.
    """
    element = element.strip().upper()
    if element not in ELEMENTAL_PROPERTIES:
        logger.warning(f"Element '{element}' not found in elemental properties database.")
        return None
    return ELEMENTAL_PROPERTIES[element].get(property_name)

def calculate_weighted_average(
    composition: Dict[str, float], 
    property_name: str,
    atomic_weights: Optional[Dict[str, float]] = None
) -> Optional[float]:
    """
    Calculate the weighted average of a property based on composition.
    
    Args:
        composition: Dict of element -> atomic fraction
        property_name: Property to average
        atomic_weights: Optional dict of element -> atomic weight (for weight-based averaging)
        
    Returns:
        Weighted average value, or None if any element is missing.
    """
    if not composition:
        return None
        
    total_weight = 0.0
    weighted_sum = 0.0
    
    for element, fraction in composition.items():
        prop_val = get_property(element, property_name)
        if prop_val is None:
            logger.warning(f"Missing property '{property_name}' for element '{element}'. Skipping composition.")
            return None
        
        weight = fraction
        if atomic_weights and element in atomic_weights:
            weight = fraction * atomic_weights[element]
        
        weighted_sum += prop_val * weight
        total_weight += weight
        
    if total_weight == 0:
        return None
        
    return weighted_sum / total_weight

def calculate_single_composition_descriptors(
    composition: Dict[str, float],
    yield_strength: Optional[float] = None,
    temperature: Optional[float] = None
) -> Optional[Dict[str, float]]:
    """
    Calculate all descriptors for a single HEA composition.
    
    Args:
        composition: Dict of element -> atomic fraction
        yield_strength: Yield strength value (optional)
        temperature: Testing temperature (optional)
        
    Returns:
        Dict of descriptor name -> value, or None if missing properties.
    """
    # Check for missing elemental properties first
    for element in composition:
        if get_property(element, 'atomic_radius') is None:
            logger.warning(f"Skipping composition: missing atomic radius for '{element}'")
            return None
        if get_property(element, 'electronegativity') is None:
            logger.warning(f"Skipping composition: missing electronegativity for '{element}'")
            return None
        if get_property(element, 'valence_electrons') is None:
            logger.warning(f"Skipping composition: missing valence electrons for '{element}'")
            return None
        if get_property(element, 'melting_point') is None:
            logger.warning(f"Skipping composition: missing melting point for '{element}'")
            return None

    # Calculate average atomic radius (r_bar)
    r_bar = calculate_weighted_average(composition, 'atomic_radius')
    if r_bar is None:
        return None

    # Calculate average electronegativity (chi_bar)
    chi_bar = calculate_weighted_average(composition, 'electronegativity')
    if chi_bar is None:
        return None

    # Calculate average valence electron concentration (VEC)
    vec = calculate_weighted_average(composition, 'valence_electrons')
    if vec is None:
        return None

    # Calculate average melting point (Tm_bar)
    t_m_bar = calculate_weighted_average(composition, 'melting_point')
    if t_m_bar is None:
        return None

    # Calculate atomic radius difference (delta)
    delta = 0.0
    for element, fraction in composition.items():
        r_i = get_property(element, 'atomic_radius')
        if r_i is None:
            return None
        delta += fraction * (1 - r_i / r_bar) ** 2
    delta = 100 * np.sqrt(delta)

    # Calculate electronegativity difference (delta_chi)
    delta_chi = 0.0
    for element, fraction in composition.items():
        chi_i = get_property(element, 'electronegativity')
        if chi_i is None:
            return None
        delta_chi += fraction * (chi_i - chi_bar) ** 2
    delta_chi = np.sqrt(delta_chi)

    # Calculate mixing entropy (delta_S_mix)
    s_mix = 0.0
    for fraction in composition.values():
        if fraction > 0:
            s_mix -= fraction * np.log(fraction)
    s_mix = 8.314 * s_mix  # R in J/(mol*K)

    # Calculate melting temperature variance (delta_Tm)
    delta_tm = 0.0
    for element, fraction in composition.items():
        t_i = get_property(element, 'melting_point')
        if t_i is None:
            return None
        delta_tm += fraction * (t_i - t_m_bar) ** 2
    delta_tm = np.sqrt(delta_tm)

    result = {
        'VEC': vec,
        'delta': delta,
        'delta_chi': delta_chi,
        'delta_S_mix': s_mix,
        'delta_Tm': delta_tm,
        'Tm_bar': t_m_bar,
    }

    if yield_strength is not None:
        result['yield_strength_MPa'] = yield_strength
    if temperature is not None:
        result['temperature_K'] = temperature

    return result

def calculate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate descriptors for a DataFrame of HEA compositions.
    
    Args:
        df: DataFrame with composition columns (e.g., 'Al', 'Cr', 'Fe') and optional 'yield_strength'
            
    Returns:
        DataFrame with added descriptor columns.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to calculate_descriptors.")
        return df

    # Identify composition columns (assumed to be element symbols)
    composition_cols = [col for col in df.columns if col.upper() in ELEMENTAL_PROPERTIES]
    
    if not composition_cols:
        logger.error("No composition columns found in DataFrame. Expected element symbols.")
        return df

    # Apply descriptor calculation row by row
    descriptors_list = []
    for idx, row in df.iterrows():
        composition = {col: row[col] for col in composition_cols if pd.notna(row[col]) and row[col] > 0}
        
        if not composition:
            logger.warning(f"Row {idx} has no valid composition data. Skipping.")
            descriptors_list.append(None)
            continue
            
        y_s = row.get('yield_strength_MPa') if 'yield_strength_MPa' in df.columns else None
        temp = row.get('temperature_K') if 'temperature_K' in df.columns else None
        
        desc = calculate_single_composition_descriptors(composition, y_s, temp)
        descriptors_list.append(desc)

    # Convert list of dicts to DataFrame
    desc_df = pd.DataFrame(descriptors_list)
    
    if desc_df.empty:
        logger.warning("No descriptors could be calculated. Resulting DataFrame is empty.")
        return df

    # Concatenate original DataFrame with descriptors
    # Drop any columns that might conflict (though we shouldn't have conflicts)
    common_cols = set(df.columns) & set(desc_df.columns)
    if common_cols:
        logger.warning(f"Dropping overlapping columns from descriptors: {common_cols}")
        desc_df = desc_df.drop(columns=list(common_cols))

    result_df = pd.concat([df.reset_index(drop=True), desc_df.reset_index(drop=True)], axis=1)
    
    logger.info(f"Calculated descriptors for {len(result_df)} rows.")
    return result_df

def filter_missing_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the DataFrame to exclude entries with missing elemental properties.
    
    This function checks if all elements present in a composition row have
    defined values for atomic_radius, electronegativity, valence_electrons,
    and melting_point in the ELEMENTAL_PROPERTIES database.
    
    Args:
        df: DataFrame with composition columns (element symbols).
        
    Returns:
        Filtered DataFrame containing only rows where all elements have
        complete property definitions.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to filter_missing_properties.")
        return df

    composition_cols = [col for col in df.columns if col.upper() in ELEMENTAL_PROPERTIES]
    
    if not composition_cols:
        logger.error("No composition columns found. Cannot filter missing properties.")
        return df

    mask = pd.Series([True] * len(df), index=df.index)
    missing_elements_log = []

    for idx, row in df.iterrows():
        for col in composition_cols:
            val = row[col]
            # Check if value is present (not NaN and > 0)
            if pd.notna(val) and val > 0:
                element = col.upper()
                # Verify all required properties exist for this element
                if element not in ELEMENTAL_PROPERTIES:
                    mask.loc[idx] = False
                    missing_elements_log.append(f"Row {idx}: Unknown element '{element}'")
                    break
                required_props = ['atomic_radius', 'electronegativity', 'valence_electrons', 'melting_point']
                for prop in required_props:
                    if prop not in ELEMENTAL_PROPERTIES[element]:
                        mask.loc[idx] = False
                        missing_elements_log.append(f"Row {idx}: Missing '{prop}' for '{element}'")
                        break
                if not mask.loc[idx]:
                    break

    if missing_elements_log:
        logger.warning(f"Found {len(missing_elements_log)} entries with missing elemental properties.")
        for msg in missing_elements_log[:5]:  # Log first 5
            logger.warning(msg)
        if len(missing_elements_log) > 5:
            logger.warning(f"... and {len(missing_elements_log) - 5} more.")

    filtered_df = df[mask].reset_index(drop=True)
    logger.info(f"Filtered {len(df) - len(filtered_df)} rows with missing elemental properties. "
                f"Remaining: {len(filtered_df)} rows.")
    
    return filtered_df