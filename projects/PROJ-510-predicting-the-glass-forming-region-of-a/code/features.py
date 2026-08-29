"""
Feature engineering for glass-forming alloy prediction.

Calculates thermodynamic descriptors: mixing enthalpy, atomic size mismatch,
and electronegativity variance based on composition and periodic table data.

FINDINGS ARE ASSOCIATIONAL: This study uses observational data; no causal claims are made.
"""

import logging
import sys
import os
from typing import List, Dict, Any, Tuple, Optional
import re
import pandas as pd
import numpy as np
from mendeleev import element

# Ensure logging is configured
logger = logging.getLogger(__name__)

def parse_composition(composition_str: str) -> List[Tuple[str, float]]:
    """
    Parse a composition string like 'Cu50Zr40Al10' into a list of (element, fraction) tuples.
    
    Args:
        composition_str: String representing alloy composition (e.g., 'Cu50Zr40Al10')
        
    Returns:
        List of (element_symbol, atomic_fraction) tuples
    """
    if not isinstance(composition_str, str):
        raise ValueError(f"Composition must be a string, got {type(composition_str)}")
        
    # Regex to match element symbols and their atomic percentages
    # Matches: Element symbol (1-2 chars) followed by numbers (float or int)
    pattern = r'([A-Z][a-z]?)(\d+(?:\.\d+)?)'
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")
        
    result = []
    for elem, frac_str in matches:
        try:
            frac = float(frac_str)
            result.append((elem, frac))
        except ValueError:
            raise ValueError(f"Invalid fraction in composition: {composition_str}")
            
    return result

def get_element_properties_safe(element_symbol: str) -> Dict[str, Any]:
    """
    Safely get elemental properties from mendeleev.
    
    Args:
        element_symbol: Chemical symbol (e.g., 'Cu', 'Fe')
        
    Returns:
        Dictionary with atomic_mass, electronegativity, atomic_radius
        
    Raises:
        ValueError: If element is not found
    """
    try:
        el = element(element_symbol)
        return {
            'symbol': el.symbol,
            'atomic_mass': el.atomic_mass,
            'electronegativity': el.electronegativity,
            'atomic_radius': el.atomic_radius
        }
    except Exception as e:
        raise ValueError(f"Element '{element_symbol}' not found in mendeleev database: {e}")

def calculate_mixing_enthalpy(composition: List[Tuple[str, float]], 
                              properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate mixing enthalpy using Miedema's model approximation.
    
    Formula: H_mix = sum_i sum_j (c_i * c_j * DeltaH_ij)
    Where c_i is atomic fraction and DeltaH_ij is interaction enthalpy.
    
    Args:
        composition: List of (element, fraction) tuples
        properties: Dictionary of element properties
        
    Returns:
        Mixing enthalpy value (dimensionless proxy)
    """
    if len(composition) < 2:
        return 0.0
        
    h_mix = 0.0
    n = len(composition)
    
    for i in range(n):
        elem_i, c_i = composition[i]
        props_i = properties[elem_i]
        
        for j in range(i + 1, n):
            elem_j, c_j = composition[j]
            props_j = properties[elem_j]
            
            # Simplified interaction term based on electronegativity difference
            # and atomic size mismatch
            chi_diff = abs(props_i['electronegativity'] - props_j['electronegativity'])
            radius_diff = abs(props_i['atomic_radius'] - props_j['atomic_radius'])
            
            # Interaction enthalpy proxy (scaled to match typical values in literature)
            # This is a simplified model for demonstration
            interaction = -10.0 * chi_diff * (1.0 + radius_diff / 10.0)
            
            h_mix += c_i * c_j * interaction
            
    return h_mix

def calculate_atomic_size_mismatch(composition: List[Tuple[str, float]], 
                                   properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate atomic size mismatch parameter (delta).
    
    Formula: delta = sqrt(sum_i (c_i * (1 - r_i / r_avg)^2))
    Where r_i is atomic radius and r_avg is average radius.
    
    Args:
        composition: List of (element, fraction) tuples
        properties: Dictionary of element properties
        
    Returns:
        Atomic size mismatch value (dimensionless)
    """
    if len(composition) < 2:
        return 0.0
        
    # Calculate weighted average radius
    r_avg = 0.0
    for elem, c in composition:
        r_avg += c * properties[elem]['atomic_radius']
        
    if r_avg == 0:
        return 0.0
        
    # Calculate mismatch
    mismatch_sum = 0.0
    for elem, c in composition:
        r_i = properties[elem]['atomic_radius']
        mismatch_sum += c * ((1.0 - r_i / r_avg) ** 2)
        
    return np.sqrt(mismatch_sum)

def calculate_electronegativity_variance(composition: List[Tuple[str, float]], 
                                         properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate electronegativity variance.
    
    Formula: chi_var = sum_i (c_i * (chi_i - chi_avg)^2)
    Where chi_i is electronegativity and chi_avg is average electronegativity.
    
    Args:
        composition: List of (element, fraction) tuples
        properties: Dictionary of element properties
        
    Returns:
        Electronegativity variance value (dimensionless)
    """
    if len(composition) < 2:
        return 0.0
        
    # Calculate weighted average electronegativity
    chi_avg = 0.0
    for elem, c in composition:
        chi_avg += c * properties[elem]['electronegativity']
        
    # Calculate variance
    chi_var_sum = 0.0
    for elem, c in composition:
        chi_i = properties[elem]['electronegativity']
        chi_var_sum += c * ((chi_i - chi_avg) ** 2)
        
    return chi_var_sum

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute thermodynamic features for all alloys in the dataframe.
    
    Adds columns:
    - mixing_enthalpy
    - atomic_size_mismatch
    - electronegativity_variance
    
    Args:
        df: DataFrame with 'composition' column
        
    Returns:
        DataFrame with added feature columns
    """
    if 'composition' not in df.columns:
        raise ValueError("Input DataFrame must have 'composition' column")
        
    logger.info(f"Computing features for {len(df)} alloys")
    
    # Initialize feature columns
    df = df.copy()
    df['mixing_enthalpy'] = np.nan
    df['atomic_size_mismatch'] = np.nan
    df['electronegativity_variance'] = np.nan
    
    failed_count = 0
    
    for idx, row in df.iterrows():
        try:
            composition_str = row['composition']
            if pd.isna(composition_str) or not isinstance(composition_str, str):
                failed_count += 1
                continue
                
            # Parse composition
            composition = parse_composition(composition_str)
            
            # Get properties for all elements
            properties = {}
            valid = True
            for elem, frac in composition:
                try:
                    properties[elem] = get_element_properties_safe(elem)
                except ValueError:
                    valid = False
                    break
                    
            if not valid or len(properties) < 2:
                failed_count += 1
                continue
                
            # Calculate features
            h_mix = calculate_mixing_enthalpy(composition, properties)
            delta = calculate_atomic_size_mismatch(composition, properties)
            chi_var = calculate_electronegativity_variance(composition, properties)
            
            df.at[idx, 'mixing_enthalpy'] = h_mix
            df.at[idx, 'atomic_size_mismatch'] = delta
            df.at[idx, 'electronegativity_variance'] = chi_var
            
        except Exception as e:
            logger.warning(f"Failed to compute features for row {idx}: {e}")
            failed_count += 1
            
    logger.info(f"Successfully computed features for {len(df) - failed_count} alloys")
    if failed_count > 0:
        logger.warning(f"Failed to compute features for {failed_count} alloys")
        
    return df

def validate_features(df: pd.DataFrame) -> bool:
    """
    Validate that computed features are reasonable.
    
    Args:
        df: DataFrame with feature columns
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If validation fails
    """
    required_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
        if df[col].isna().any():
            raise ValueError(f"Column {col} contains NaN values")
            
        if df[col].var() == 0:
            raise ValueError(f"Column {col} has zero variance")
            
    return True

def run_features(input_path: str, output_path: str) -> None:
    """
    Main entry point for feature computation script.
    
    Args:
        input_path: Path to input CSV with composition data
        output_path: Path to save output CSV with features
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info("Computing thermodynamic features")
    df_features = compute_features(df)
    
    logger.info(f"Validating features")
    validate_features(df_features)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    df_features.to_csv(output_path, index=False)
    
    logger.info("Feature computation completed successfully")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python features.py <input_csv> <output_csv>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    run_features(input_file, output_file)
