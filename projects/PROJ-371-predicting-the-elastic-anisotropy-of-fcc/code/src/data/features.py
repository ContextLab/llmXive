"""
Feature engineering module for computing compositional descriptors.

Computes atomic radius variance, electronegativity standard deviation,
and valence electron concentration from chemical formulas.
"""
import sys
import logging
from typing import List, Optional, Dict, Any, Tuple
import re
import pandas as pd
import numpy as np
from mendeleev import element as mendeleev_element

logger = logging.getLogger(__name__)

# Constants for feature calculation
DESCRIPTOR_COLUMNS = [
    'atomic_radius_variance',
    'electronegativity_std',
    'valence_electron_concentration'
]

def parse_formula(formula: str) -> Dict[str, float]:
    """
    Parse a chemical formula into a dictionary of element symbols and their counts.
    
    Handles standard chemical formula notation (e.g., "Cu", "Al2O3", "FeNi3").
    
    Args:
        formula: Chemical formula string (e.g., "Cu", "Al2O3", "FeNi3")
        
    Returns:
        Dictionary mapping element symbols to their stoichiometric counts
        
    Raises:
        ValueError: If formula cannot be parsed
    """
    if not formula or not isinstance(formula, str):
        raise ValueError(f"Invalid formula: {formula}")
        
    formula = formula.strip()
    if not formula:
        raise ValueError("Empty formula string")
    
    # Pattern to match element symbols and optional counts
    # Element symbols: Capital letter followed by optional lowercase letter(s)
    # Count: Optional digits following the element
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, formula)
    
    if not matches:
        raise ValueError(f"Could not parse formula: {formula}")
    
    elements = {}
    for symbol, count_str in matches:
        count = int(count_str) if count_str else 1
        elements[symbol] = count
    
    return elements

def get_valence_electrons(symbol: str) -> Optional[int]:
    """
    Get the number of valence electrons for an element.
    
    Uses the group number for main group elements (groups 1, 2, 13-18).
    For transition metals, uses the number of electrons in the outermost s and d shells.
    
    Args:
        symbol: Element symbol (e.g., "Cu", "Fe")
        
    Returns:
        Number of valence electrons, or None if element not found
    """
    try:
        elem = mendeleev_element(symbol)
        # Use the group number for valence electrons
        # For transition metals, this gives the group number (which corresponds to
        # the number of valence electrons in the s and d shells)
        if elem.group is not None:
            group = elem.group
            # Main group elements: groups 1, 2, 13-18
            if group <= 2:
                return group
            elif group >= 13:
                return group - 10  # Groups 13-18 map to 3-8 valence electrons
            else:
                # Transition metals: use group number directly
                return group
        else:
            logger.warning(f"Group information missing for element {symbol}")
            return None
    except Exception as e:
        logger.warning(f"Could not get valence electrons for {symbol}: {e}")
        return None

def get_element_properties(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get atomic properties for an element.
    
    Args:
        symbol: Element symbol (e.g., "Cu", "Fe")
        
    Returns:
        Dictionary with 'atomic_radius' (in pm) and 'electronegativity' (Pauling scale),
        or None if element not found
    """
    try:
        elem = mendeleev_element(symbol)
        
        # Get atomic radius (covalent radius in pm)
        atomic_radius = elem.covalent_radius
        if atomic_radius is None:
            # Try van der Waals radius if covalent is not available
            atomic_radius = elem.van_der_waals_radius
        
        # Get electronegativity (Pauling scale)
        electronegativity = elem.electronegativity
        
        if atomic_radius is None or electronegativity is None:
            logger.warning(f"Missing properties for element {symbol}")
            return None
        
        return {
            'atomic_radius': float(atomic_radius),
            'electronegativity': float(electronegativity)
        }
    except Exception as e:
        logger.warning(f"Could not get properties for {symbol}: {e}")
        return None

def compute_compositional_features(formula: str) -> Optional[Dict[str, float]]:
    """
    Compute compositional features for a chemical formula.
    
    Calculates:
    - Atomic radius variance: Variance of atomic radii weighted by stoichiometry
    - Electronegativity std: Standard deviation of electronegativities weighted by stoichiometry
    - Valence electron concentration: Average number of valence electrons per atom
    
    Args:
        formula: Chemical formula string
        
    Returns:
        Dictionary with computed features, or None if computation fails
    """
    try:
        # Parse formula
        elements = parse_formula(formula)
        if not elements:
            return None
        
        total_atoms = sum(elements.values())
        if total_atoms == 0:
            return None
        
        # Collect properties
        atomic_radii = []
        electronegativities = []
        valence_electrons = []
        weights = []
        
        for symbol, count in elements.items():
            props = get_element_properties(symbol)
            if props is None:
                logger.warning(f"Skipping formula {formula} due to missing properties for {symbol}")
                return None
            
            valence = get_valence_electrons(symbol)
            if valence is None:
                logger.warning(f"Skipping formula {formula} due to missing valence for {symbol}")
                return None
            
            atomic_radii.append(props['atomic_radius'])
            electronegativities.append(props['electronegativity'])
            valence_electrons.append(valence)
            weights.append(count)
        
        # Convert to numpy arrays for weighted calculations
        radii = np.array(atomic_radii)
        electronegs = np.array(electronegativities)
        valences = np.array(valence_electrons)
        weights = np.array(weights)
        
        # Normalize weights
        weights_normalized = weights / total_atoms
        
        # Calculate weighted mean and variance/std
        mean_radius = np.average(radii, weights=weights_normalized)
        radius_variance = np.average((radii - mean_radius) ** 2, weights=weights_normalized)
        
        mean_electroneg = np.average(electronegs, weights=weights_normalized)
        electroneg_std = np.sqrt(np.average((electronegs - mean_electroneg) ** 2, weights=weights_normalized))
        
        # Valence electron concentration (average valence electrons per atom)
        vec = np.average(valences, weights=weights_normalized)
        
        return {
            'atomic_radius_variance': float(radius_variance),
            'electronegativity_std': float(electroneg_std),
            'valence_electron_concentration': float(VEC)
        }
        
    except Exception as e:
        logger.error(f"Error computing features for formula {formula}: {e}")
        return None

def add_features_to_dataframe(df: pd.DataFrame, formula_column: str = 'formula') -> pd.DataFrame:
    """
    Add compositional features to a DataFrame.
    
    Args:
        df: Input DataFrame with a 'formula' column
        formula_column: Name of the column containing chemical formulas
        
    Returns:
        DataFrame with added feature columns
    """
    logger.info(f"Computing compositional features for {len(df)} entries")
    
    # Initialize new columns with NaN
    for col in DESCRIPTOR_COLUMNS:
        df[col] = np.nan
    
    # Process each row
    valid_count = 0
    failed_count = 0
    
    for idx, row in df.iterrows():
        formula = row[formula_column]
        features = compute_compositional_features(formula)
        
        if features is not None:
            for col, value in features.items():
                df.at[idx, col] = value
            valid_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Feature computation: {valid_count} successful, {failed_count} failed")
    
    # Check for any remaining NaN values
    nan_counts = df[DESCRIPTOR_COLUMNS].isna().sum()
    if nan_counts.any():
        logger.warning(f"NaN values in feature columns: {nan_counts.to_dict()}")
    
    return df

def main():
    """Main function to run feature engineering on cleaned data."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    input_path = Path('data/processed/cleaned_elastic_data.csv')
    output_path = Path('data/processed/elastic_anisotropy.csv')
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load cleaned data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'formula' not in df.columns:
        logger.error("Input data must contain a 'formula' column")
        sys.exit(1)
    
    # Compute features
    df_with_features = add_features_to_dataframe(df, 'formula')
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    df_with_features.to_csv(output_path, index=False)
    
    logger.info(f"Feature engineering complete. Output: {output_path}")
    logger.info(f"Output shape: {df_with_features.shape}")
    logger.info(f"Columns: {list(df_with_features.columns)}")

if __name__ == '__main__':
    main()
