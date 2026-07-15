"""
Metallic Glass Descriptor Calculation Module.

Computes atomic descriptors including radius mismatch, electronegativity difference,
valence electron concentration (VEC), and weighted mean radius for diagnostic logging.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

# Import mendeleev for elemental properties
# Note: mendeleev==0.31.0 is required per FR-002
try:
    from mendeleev import element
    from mendeleev.models import Element
except ImportError:
    raise ImportError(
        "The 'mendeleev' package is required for descriptor calculation. "
        "Please install it with: pip install mendeleev==0.31.0"
    )

# Configure logging
logger = logging.getLogger(__name__)

# Constants for atomic radius calculation
# Using covalent radii as the primary metric for metallic glasses
RADIUS_TYPE = 'covalent_radius' 

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """
    Retrieve atomic properties for a given element symbol.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Zr')
        
    Returns:
        Dictionary containing atomic number, radius, electronegativity, and VEC.
        
    Raises:
        ValueError: If the element symbol is invalid.
    """
    symbol = symbol.strip().capitalize()
    try:
        el = element(symbol)
        # Mendeleev returns None for some properties if not available
        radius = getattr(el, RADIUS_TYPE, None)
        if radius is None:
            # Fallback to atomic_radius if covalent is missing
            radius = getattr(el, 'atomic_radius', None)
            
        electronegativity = getattr(el, 'electronegativity', None)
        
        # VEC (Valence Electron Concentration) calculation
        # For transition metals, VEC is often approximated by group number
        # Mendeleev doesn't have a direct VEC property, so we calculate it
        # based on the electron configuration
        vec = None
        if el is not None:
            # Use group number as a proxy for VEC for transition metals
            # This is a common approximation in MG research
            vec = el.group
            if vec is None:
                # Fallback for elements without a clear group
                vec = el.n_valence if hasattr(el, 'n_valence') else 0
                
        return {
            'symbol': symbol,
            'atomic_number': el.atomic_number,
            'radius': radius,
            'electronegativity': electronegativity,
            'vec': vec,
            'element': el
        }
    except Exception as e:
        raise ValueError(f"Invalid element symbol '{symbol}': {e}")

def calculate_weighted_mean_radius(row: pd.Series, composition_col: str = 'composition') -> float:
    """
    Calculate the weighted mean atomic radius for a given composition.
    
    This is a diagnostic metric only (FR-002) and is excluded from model training.
    It represents the average atomic size of the alloy weighted by atomic fraction.
    
    Args:
        row: A row from the DataFrame containing the composition string.
        composition_col: Name of the column containing the composition string.
        
    Returns:
        Weighted mean radius in Angstroms.
        
    Raises:
        ValueError: If composition parsing fails or an element is not found.
    """
    comp_str = row[composition_col]
    if not isinstance(comp_str, str) or not comp_str.strip():
        raise ValueError(f"Invalid composition string: {comp_str}")
        
    # Parse composition string (e.g., "Zr40Cu60" -> {"Zr": 0.4, "Cu": 0.6})
    # Expected format: ElementSymbol followed by percentage (no separator)
    import re
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, comp_str)
    
    if not matches:
        raise ValueError(f"Could not parse composition: {comp_str}")
        
    total_weight = 0.0
    weighted_radius_sum = 0.0
    
    for symbol, amount in matches:
        try:
            props = get_element_properties(symbol)
            radius = props['radius']
            if radius is None:
                logger.warning(f"Radius not found for {symbol}, skipping in weighted mean.")
                continue
                
            weight = float(amount)
            total_weight += weight
            weighted_radius_sum += weight * radius
        except ValueError as e:
            logger.warning(f"Skipping element {symbol} in weighted mean calculation: {e}")
            continue
            
    if total_weight == 0:
        raise ValueError("No valid elements found in composition for weighted mean radius.")
        
    return weighted_radius_sum / total_weight

def calculate_radius_mismatch(row: pd.Series, composition_col: str = 'composition') -> float:
    """
    Calculate the atomic radius mismatch (δ) for a metallic glass.
    
    δ = sqrt(Σ c_i (1 - r_i / r_avg)^2) * 100
    where c_i is the atomic fraction and r_i is the atomic radius.
    
    Args:
        row: A row from the DataFrame.
        composition_col: Name of the composition column.
        
    Returns:
        Radius mismatch percentage.
    """
    comp_str = row[composition_col]
    import re
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, comp_str)
    
    radii = []
    weights = []
    
    for symbol, amount in matches:
        try:
            props = get_element_properties(symbol)
            radius = props['radius']
            if radius is not None:
                radii.append(radius)
                weights.append(float(amount))
        except ValueError:
            continue
            
    if not radii:
        return 0.0
        
    # Normalize weights to fractions
    total_weight = sum(weights)
    fractions = [w / total_weight for w in weights]
    
    # Calculate weighted mean radius
    r_avg = sum(f * r for f, r in zip(fractions, radii))
    
    if r_avg == 0:
        return 0.0
        
    # Calculate mismatch
    mismatch_sum = sum(
        f * ((1 - (r / r_avg)) ** 2) 
        for f, r in zip(fractions, radii)
    )
    
    return (mismatch_sum ** 0.5) * 100

def calculate_electronegativity_difference(row: pd.Series, composition_col: str = 'composition') -> float:
    """
    Calculate the electronegativity difference (Δχ) for a metallic glass.
    
    Δχ = sqrt(Σ c_i c_j (χ_i - χ_j)^2) for i < j
    where c_i is the atomic fraction and χ_i is the electronegativity.
    
    Args:
        row: A row from the DataFrame.
        composition_col: Name of the composition column.
        
    Returns:
        Electronegativity difference.
    """
    comp_str = row[composition_col]
    import re
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, comp_str)
    
    electronegativities = []
    weights = []
    
    for symbol, amount in matches:
        try:
            props = get_element_properties(symbol)
            en = props['electronegativity']
            if en is not None:
                electronegativities.append(en)
                weights.append(float(amount))
        except ValueError:
            continue
            
    if len(electronegativities) < 2:
        return 0.0
        
    # Normalize weights
    total_weight = sum(weights)
    fractions = [w / total_weight for w in weights]
    
    # Calculate pairwise difference
    diff_sum = 0.0
    for i in range(len(fractions)):
        for j in range(i + 1, len(fractions)):
            diff_sum += fractions[i] * fractions[j] * (electronegativities[i] - electronegativities[j]) ** 2
            
    return diff_sum ** 0.5

def calculate_vec(row: pd.Series, composition_col: str = 'composition') -> float:
    """
    Calculate the Valence Electron Concentration (VEC) for a metallic glass.
    
    VEC = Σ c_i * VEC_i
    where c_i is the atomic fraction and VEC_i is the valence electron count.
    
    Args:
        row: A row from the DataFrame.
        composition_col: Name of the composition column.
        
    Returns:
        Weighted average VEC.
    """
    comp_str = row[composition_col]
    import re
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, comp_str)
    
    vecs = []
    weights = []
    
    for symbol, amount in matches:
        try:
            props = get_element_properties(symbol)
            vec = props['vec']
            if vec is not None:
                vecs.append(vec)
                weights.append(float(amount))
        except ValueError:
            continue
            
    if not vecs:
        return 0.0
        
    total_weight = sum(weights)
    fractions = [w / total_weight for w in weights]
    
    return sum(f * v for f, v in zip(fractions, vecs))

def compute_descriptors(df: pd.DataFrame, composition_col: str = 'composition') -> pd.DataFrame:
    """
    Compute all descriptors for a DataFrame of metallic glass compositions.
    
    Args:
        df: Input DataFrame with a composition column.
        composition_col: Name of the composition column.
        
    Returns:
        DataFrame with added descriptor columns.
    """
    df = df.copy()
    
    logger.info(f"Computing descriptors for {len(df)} records...")
    
    # Calculate descriptors
    df['radius_mismatch'] = df.apply(calculate_radius_mismatch, axis=1, args=(composition_col,))
    df['electronegativity_diff'] = df.apply(calculate_electronegativity_difference, axis=1, args=(composition_col,))
    df['vec'] = df.apply(calculate_vec, axis=1, args=(composition_col,))
    
    # Calculate weighted mean radius (DIAGNOSTIC ONLY - FR-002)
    # This is excluded from model training but logged for diagnostics
    logger.info("Calculating weighted mean radius for diagnostic logging...")
    df['weighted_mean_radius'] = df.apply(calculate_weighted_mean_radius, axis=1, args=(composition_col,))
    
    # Log summary statistics for the diagnostic metric
    wmr_stats = df['weighted_mean_radius'].describe()
    logger.info(f"Weighted Mean Radius Statistics:\n{wmr_stats}")
    
    return df

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame to add all necessary descriptors.
    
    This is a convenience wrapper around compute_descriptors.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Processed DataFrame with descriptors.
    """
    return compute_descriptors(df)

def main():
    """
    Main entry point for running descriptor calculation as a script.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage:
    # This would typically be called by the training pipeline
    logger.info("Descriptor calculation module loaded successfully.")
    logger.info("Use compute_descriptors(df) to calculate descriptors for a DataFrame.")

if __name__ == "__main__":
    main()