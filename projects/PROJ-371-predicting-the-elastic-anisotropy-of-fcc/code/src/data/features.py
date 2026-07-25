"""
Feature Engineering Module for Elastic Anisotropy Prediction.

Computes compositional descriptors (atomic radius variance, electronegativity std dev,
valence electron concentration) from chemical formulas using the mendeleev library.
"""
import sys
import logging
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from mendeleev import element as mendeleev_element

# Import local config for paths if needed, though standard paths are used here
# from src.utils.config import get_path

logger = logging.getLogger(__name__)

# Constants for element property retrieval
# Mendeleev uses 'atomic_radius' (empirical) or 'covalent_radius' (calculated).
# We use 'atomic_radius' (empirical) as it's standard for metallic descriptors.
# We use 'electronegativity' (Pauling scale).
# We use 'n_electrons' and 'atomic_number' to derive valence electrons for main group/transition metals.
# For transition metals, valence is often defined as group number or specific oxidation state.
# A common heuristic in materials science for VEC is: sum(valence_i * fraction_i).
# We will use the group number (1-18) mapped to typical valence electrons for metals:
# Group 1: 1, Group 2: 2, Group 3-12: Group number - 10 (e.g. Sc=3, Ti=4... Zn=12 -> 2? No, Zn is often 2).
# Actually, a robust method for VEC in alloys (like FCC) often uses:
# VEC = sum(c_i * v_i) where v_i is the number of valence electrons.
# For transition metals, v_i is often taken as the number of s+d electrons.
# Mendeleev doesn't have a direct "valence_electrons" property that is consistent across all oxidation states.
# We will use a heuristic:
# - For Groups 1, 2: Group number
# - For Groups 3-12: Group number (e.g. Sc=3, Ti=4, V=5, Cr=6, Mn=7, Fe=8, Co=9, Ni=10, Cu=11, Zn=12).
#   *Note*: Some literature uses 2 for Zn, but 12 is the total s+d count.
#   Let's stick to the Group Number as the valence count for transition metals in alloy contexts (e.g. Cantor alloys).
# - For Groups 13-18: Group number - 10 (e.g. Al=3, Ga=3).

def get_valence_electrons(symbol: str) -> int:
    """
    Heuristic to estimate valence electrons for alloy composition calculations.
    Uses Mendeleev data.
    """
    try:
        el = mendeleev_element(symbol)
        group = el.group
        if group is None:
            # Fallback for elements not in a standard group (rare)
            logger.warning(f"Element {symbol} has no group. Defaulting to 1.")
            return 1
        
        if 1 <= group <= 2:
            return group
        elif 3 <= group <= 12:
            # Transition metals: typically use group number as valence count in alloys
            return group
        elif 13 <= group <= 18:
            return group - 10
        else:
            # Fallback
            return 1
    except Exception as e:
        logger.error(f"Error retrieving valence for {symbol}: {e}")
        return 1

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """
    Retrieve atomic radius and electronegativity for a given element symbol.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu').
        
    Returns:
        Dict with 'radius' (Angstrom), 'electronegativity' (Pauling), 'valence'.
        Returns None if element not found or properties missing.
    """
    try:
        el = mendeleev_element(symbol)
        
        # Atomic radius (empirical) in Angstroms
        # Mendeleev stores this as 'atomic_radius'
        radius = el.atomic_radius
        if radius is None:
            # Try covalent radius as fallback
            radius = el.covalent_radius
            if radius is None:
                logger.warning(f"Missing atomic/covalent radius for {symbol}")
                return None
        
        # Electronegativity (Pauling)
        electronegativity = el.electronegativity
        if electronegativity is None:
            logger.warning(f"Missing electronegativity for {symbol}")
            return None
        
        valence = get_valence_electrons(symbol)
        
        return {
            'radius': float(radius),
            'electronegativity': float(electronegativity),
            'valence': valence
        }
    except Exception as e:
        logger.error(f"Failed to get properties for {symbol}: {e}")
        return None

def parse_formula(formula: str) -> Dict[str, float]:
    """
    Parse a simple chemical formula (e.g., 'Fe', 'Al0.5CoCrFeNi') into element fractions.
    Assumes no complex nested parentheses for this MVP.
    Handles formulas like 'Fe', 'Cu', 'Al0.5Co0.5'.
    """
    import re
    
    # Pattern to match element symbol followed by optional number
    # Elements are [A-Z][a-z]?
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, formula)
    
    fractions = {}
    total_atoms = 0.0
    
    for symbol, count_str in matches:
        count = float(count_str) if count_str else 1.0
        fractions[symbol] = count
        total_atoms += count
    
    # Normalize to fractions
    if total_atoms == 0:
        return {}
        
    return {k: v / total_atoms for k, v in fractions.items()}

def compute_compositional_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute compositional descriptors for the dataframe.
    
    Adds columns:
    - atomic_radius_variance: Variance of atomic radii weighted by composition.
    - electronegativity_std: Standard deviation of electronegativity weighted by composition.
    - valence_electron_concentration (VEC): Weighted average of valence electrons.
    
    Args:
        df: DataFrame with a 'formula' column and potentially other columns.
        
    Returns:
        DataFrame with new feature columns added.
    """
    logger.info("Starting feature computation...")
    
    radius_list = []
    electronegativity_list = []
    valence_list = []
    skipped_rows = 0
    
    results = []
    
    for idx, row in df.iterrows():
        formula = row.get('formula')
        if not formula or pd.isna(formula):
            logger.warning(f"Row {idx}: Missing formula. Skipping features.")
            skipped_rows += 1
            # Append NaNs or keep original? Let's keep original with NaN features
            results.append({
                'atomic_radius_variance': np.nan,
                'electronegativity_std': np.nan,
                'valence_electron_concentration': np.nan
            })
            continue
        
        try:
            fractions = parse_formula(str(formula))
            if not fractions:
                raise ValueError("Could not parse formula")
            
            radii = []
            en_values = []
            valences = []
            weights = []
            
            valid_element = True
            for elem, frac in fractions.items():
                props = get_element_properties(elem)
                if props is None:
                    valid_element = False
                    logger.warning(f"Row {idx}: Missing properties for {elem}. Skipping row.")
                    break
                radii.append(props['radius'])
                en_values.append(props['electronegativity'])
                valences.append(props['valence'])
                weights.append(frac)
            
            if not valid_element:
                results.append({
                    'atomic_radius_variance': np.nan,
                    'electronegativity_std': np.nan,
                    'valence_electron_concentration': np.nan
                })
                skipped_rows += 1
                continue
            
            # Calculate weighted mean
            weights = np.array(weights)
            radii = np.array(radii)
            en_values = np.array(en_values)
            valences = np.array(valences)
            
            mean_radius = np.average(radii, weights=weights)
            mean_en = np.average(en_values, weights=weights)
            mean_valence = np.average(valences, weights=weights)
            
            # Calculate weighted variance/std
            # Variance = sum(w * (x - mean)^2)
            radius_variance = np.average((radii - mean_radius)**2, weights=weights)
            en_std = np.sqrt(np.average((en_values - mean_en)**2, weights=weights))
            
            results.append({
                'atomic_radius_variance': radius_variance,
                'electronegativity_std': en_std,
                'valence_electron_concentration': mean_valence
            })
            
        except Exception as e:
            logger.error(f"Row {idx}: Error processing formula '{formula}': {e}")
            results.append({
                'atomic_radius_variance': np.nan,
                'electronegativity_std': np.nan,
                'valence_electron_concentration': np.nan
            })
            skipped_rows += 1
    
    # Create new dataframe with features
    features_df = pd.DataFrame(results)
    combined_df = pd.concat([df.reset_index(drop=True), features_df], axis=1)
    
    logger.info(f"Feature computation complete. Skipped {skipped_rows} rows.")
    return combined_df

def main():
    """
    Main entry point for running feature engineering on the processed dataset.
    Reads from data/processed/elastic_anisotropy.csv (cleaned) and writes to data/processed/elastic_anisotropy_features.csv.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    # Assuming project root is 'code' relative to where this runs, or we use absolute paths from config
    # Since we don't have the full config loaded here, we assume standard paths relative to script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    input_path = project_root / 'data' / 'processed' / 'elastic_anisotropy.csv'
    output_path = project_root / 'data' / 'processed' / 'elastic_anisotropy_features.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Reading input from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input CSV: {e}")
        sys.exit(1)
    
    # Check for formula column
    if 'formula' not in df.columns:
        logger.error("Input CSV must contain a 'formula' column.")
        sys.exit(1)
    
    logger.info(f"Processing {len(df)} rows...")
    df_features = compute_compositional_features(df)
    
    logger.info(f"Writing output to {output_path}")
    df_features.to_csv(output_path, index=False)
    
    logger.info("Feature engineering completed successfully.")

if __name__ == "__main__":
    main()
