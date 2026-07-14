"""
Feature engineering module for compositional descriptors.

Computes atomic radius variance, electronegativity standard deviation,
and valence electron concentration (VEC) using the mendeleev library.
"""

import sys
import logging
from typing import List, Optional
import pandas as pd
from mendeleev import element

from src.utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def get_element_properties(symbol: str) -> Optional[dict]:
    """
    Fetch atomic properties for a single element.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu')
        
    Returns:
        Dict with 'radius' and 'electronegativity' or None if not found.
    """
    try:
        el = element(symbol)
        # Mendeleev property names might vary, using common ones
        # radius: covalent_radius or atomic_radius
        # electronegativity: pauling_scale
        
        radius = el.covalent_radius if el.covalent_radius else el.atomic_radius
        electronegativity = el.pauling_scale if el.pauling_scale else 0.0
        
        if radius is None:
            log_warning(f"Missing radius for {symbol}")
            return None
            
        return {
            "radius": radius,
            "electronegativity": electronegativity,
            "valence": el.valence if el.valence else 0 # Mendeleev valence might be a list or int
        }
    except Exception as e:
        log_warning(f"Could not fetch properties for {symbol}: {str(e)}")
        return None

def compute_compositional_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Compute compositional descriptors for the input dataframe.
    
    Expected input columns: 'formula' (or 'element' if single element)
    Output columns: 'radius_variance', 'electronegativity_std', 'vec'
    
    For FCC metals in this simplified pipeline, we assume single-element
    or simple alloys. We will parse the formula to get constituent elements.
    """
    if df is None or df.empty:
        log_error("Input dataframe is empty.")
        return None

    log_info("Computing compositional features...")
    
    # Simple formula parser for single elements or binary/ternary
    # Format: "Cu", "Fe3Al", etc.
    # For this specific task (FCC metals), we often have pure metals.
    # If it's an alloy, we calculate weighted averages.
    
    def parse_formula(formula: str) -> List[tuple]:
        """Simple parser for element symbols and counts."""
        import re
        # Regex to match element symbol and optional count
        pattern = re.compile(r"([A-Z][a-z]*)(\d*)")
        matches = pattern.findall(formula)
        result = []
        for symbol, count in matches:
            count = int(count) if count else 1
            result.append((symbol, count))
        return result

    def calculate_features(formula: str):
        elements = parse_formula(formula)
        if not elements:
            return None, None, None

        total_count = sum(count for _, count in elements)
        
        radii = []
        en_values = []
        valence_counts = []
        
        for symbol, count in elements:
            props = get_element_properties(symbol)
            if props:
                radii.extend([props['radius']] * count)
                en_values.extend([props['electronegativity']] * count)
                # Valence electron concentration: sum of valence electrons / total atoms
                # Mendeleev 'valence' might be complex, using a simplified approach
                # For pure metals, VEC is just the group number or valence electrons.
                # We'll use the property if available, else 0.
                valence_counts.append(props['valence'] * count)
            else:
                # If one element fails, we might still proceed if others exist, 
                # but for strictness, let's flag it.
                log_warning(f"Skipping feature calc for {formula} due to missing {symbol}")
                return None, None, None

        if not radii:
            return None, None, None

        # Variance of atomic radii
        import numpy as np
        radius_variance = np.var(radii)
        
        # Std dev of electronegativity
        en_std = np.std(en_values)
        
        # VEC: weighted average of valence electrons
        total_valence = sum(valence_counts)
        vec = total_valence / total_count

        return radius_variance, en_std, vec

    # Apply feature calculation
    features = df['formula'].apply(calculate_features)
    
    # Split the tuple results into columns
    df['radius_variance'] = [f[0] for f in features]
    df['electronegativity_std'] = [f[1] for f in features]
    df['vec'] = [f[2] for f in features]

    # Drop rows where features couldn't be calculated
    initial_len = len(df)
    df = df.dropna(subset=['radius_variance', 'electronegativity_std', 'vec'])
    dropped = initial_len - len(df)
    if dropped > 0:
        log_warning(f"Dropped {dropped} rows due to feature calculation failure.")

    log_info(f"Features computed. Final shape: {df.shape}")
    return df

def main():
    """Test the feature computation."""
    # Dummy data for testing
    test_df = pd.DataFrame({
        'formula': ['Cu', 'Al', 'Fe', 'Ni']
    })
    result = compute_compositional_features(test_df)
    if result is not None:
        print(result)
    else:
        print("Failed to compute features.")
        sys.exit(1)

if __name__ == "__main__":
    main()
