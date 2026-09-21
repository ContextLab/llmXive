import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np

# Import from project structure relative to code/ root
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution or different import context
    import logging as builtin_logging
    def get_logger(name):
        return builtin_logging.getLogger(name)

logger = get_logger(__name__)

# Constants
ELEMENTS_FILE = Path("data/config/elements.yaml")
KNOWN_ELEMENTS = set()

def _load_known_elements():
    """Load the set of known abundant elements from config."""
    global KNOWN_ELEMENTS
    if not KNOWN_ELEMENTS:
        if ELEMENTS_FILE.exists():
            import yaml
            with open(ELEMENTS_FILE, 'r') as f:
                data = yaml.safe_load(f)
                if 'elements' in data:
                    KNOWN_ELEMENTS = set(data['elements'])
        else:
            # Fallback to a standard set if file missing, though T008b should have created it
            KNOWN_ELEMENTS = {
                'Al', 'Ca', 'Fe', 'Mg', 'Ti', 'Na', 'K', 'Zn', 'Si', 'Zr',
                'Cu', 'Ni', 'Cr', 'Mn', 'V', 'Sn', 'Pb', 'Ag', 'Au', 'Pd',
                'Pt', 'Mo', 'W', 'Nb', 'Ta', 'Hf', 'Y', 'La', 'Ce', 'Sc'
            }
    return KNOWN_ELEMENTS

def get_element_properties(element: str) -> Dict[str, float]:
    """
    Fetch atomic properties for a given element using Pymatgen.
    
    Args:
        element: Element symbol (e.g., 'Cu')
        
    Returns:
        Dictionary containing 'atomic_radius', 'electronegativity', 'VEC'
    """
    try:
        from pymatgen.core import Element
        el = Element(element)
        
        # Get properties
        atomic_radius = el.atomic_radius
        electronegativity = el.data.get('electronegativity', 0.0) # Pauling scale
        
        # Calculate VEC (Valence Electron Concentration)
        # Pymatgen doesn't have a direct VEC property, so we calculate it from group number
        # or use a standard lookup. For transition metals, VEC is often group number.
        # We'll use the number of valence electrons.
        # Pymatgen Element has 'valence_electrons' in some versions, but let's be safe.
        # Standard approach: Group number for main group, d-electrons + s-electrons for transition.
        # Using a simplified approach based on standard periodic table values for GFA studies.
        
        # Fallback calculation if direct property is missing
        if el.group == 0:
            vec = 0
        elif el.group == 1:
            vec = 1
        elif el.group == 2:
            vec = 2
        elif el.group == 13:
            vec = 3
        elif el.group == 14:
            vec = 4
        elif el.group == 15:
            vec = 5
        elif el.group == 16:
            vec = 6
        elif el.group == 17:
            vec = 7
        elif el.group == 18:
            vec = 8
        else:
            # Transition metals: often use group number (3-12) as VEC in GFA literature
            # e.g., Ti (4), V (5), Cr (6), Mn (7), Fe (8), Co (9), Ni (10)
            vec = el.group
        
        # Correction for some specific elements if standard group number is not the GFA convention
        # But for general implementation, group number is the standard proxy.
        
        return {
            'atomic_radius': atomic_radius if atomic_radius is not None else 0.0,
            'electronegativity': electronegativity if electronegativity is not None else 0.0,
            'VEC': float(vec)
        }
    except Exception as e:
        logger.error(f"Failed to get properties for element {element}: {e}")
        # Return zeros to avoid crashing, but log the error
        return {'atomic_radius': 0.0, 'electronegativity': 0.0, 'VEC': 0.0}

def parse_composition_string(comp_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Cu50Zr40Al10' into a dict of {element: fraction}.
    
    Args:
        comp_str: String representation of composition
        
    Returns:
        Dictionary mapping element symbols to their atomic fractions
    """
    import re
    # Regex to match Element symbol followed by optional number
    # Handles cases like 'Cu50', 'Zr', 'Al10.5'
    pattern = re.compile(r'([A-Z][a-z]*)(\d*\.?\d*)')
    matches = pattern.findall(comp_str)
    
    composition = {}
    total = 0.0
    
    for elem, frac_str in matches:
        if not frac_str:
            # If no number, assume 1 (or handle as error? Spec implies valid input)
            # Usually compositions sum to 100, so 1 might be wrong.
            # Let's assume standard input format is Element + Number.
            # If missing, we might need to normalize later.
            frac = 1.0
        else:
            frac = float(frac_str)
        
        composition[elem] = frac
        total += frac
    
    # Normalize to sum to 1.0
    if total > 0:
        composition = {k: v/total for k, v in composition.items()}
    
    return composition

def compute_weighted_mean(values: List[float], weights: List[float]) -> float:
    """Compute weighted mean of a list of values."""
    if not values or not weights:
        return 0.0
    return np.average(values, weights=weights)

def compute_weighted_variance(values: List[float], weights: List[float]) -> float:
    """Compute weighted variance of a list of values."""
    if not values or not weights:
        return 0.0
    mean = compute_weighted_mean(values, weights)
    variance = np.average((np.array(values) - mean)**2, weights=weights)
    return variance

def compute_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Compute the atomic size mismatch parameter (delta).
    Formula: sqrt( sum( ci * (1 - ri/r_avg)^2 ) )
    
    Args:
        composition: Dict of {element: fraction}
        
    Returns:
        Size mismatch value
    """
    elements = list(composition.keys())
    fractions = list(composition.values())
    
    radii = []
    for el in elements:
        props = get_element_properties(el)
        if props['atomic_radius'] == 0.0:
            logger.warning(f"Unknown radius for {el}, skipping size mismatch calculation for this row.")
            return 0.0
        radii.append(props['atomic_radius'])
    
    r_avg = compute_weighted_mean(radii, fractions)
    if r_avg == 0:
        return 0.0
    
    delta_sq = 0.0
    for c_i, r_i in zip(fractions, radii):
        delta_sq += c_i * (1 - r_i / r_avg)**2
    
    return np.sqrt(delta_sq)

def compute_pairwise_size_mismatch(composition: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Compute pairwise size mismatch descriptors for every unique pair of elements.
    
    For a composition A-B-C, calculates pairs: (A,B), (A,C), (B,C).
    Returns a list of dictionaries with pair info and mismatch value.
    
    Args:
        composition: Dict of {element: fraction}
        
    Returns:
        List of dicts: [{'pair': 'A-B', 'mismatch': value}, ...]
    """
    elements = list(composition.keys())
    if len(elements) < 2:
        return []
    
    pairs = []
    radii = {}
    
    # Fetch radii for all elements first
    for el in elements:
        props = get_element_properties(el)
        if props['atomic_radius'] == 0.0:
            logger.warning(f"Unknown radius for {el} in pairwise calculation.")
            return []
        radii[el] = props['atomic_radius']
    
    # Iterate over unique pairs
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            el1, el2 = elements[i], elements[j]
            r1, r2 = radii[el1], radii[el2]
            
            # Pairwise size mismatch: |r1 - r2| / max(r1, r2)
            # Or (r1 - r2)^2 / r1*r2 ? 
            # Common GFA descriptor: |r1 - r2| / r_avg_pair
            # Let's use the standard definition: |r1 - r2| / max(r1, r2)
            mismatch = abs(r1 - r2) / max(r1, r2)
            
            pair_name = f"{el1}-{el2}" if el1 < el2 else f"{el2}-{el1}"
            pairs.append({
                'pair': pair_name,
                'mismatch': mismatch,
                'r1': r1,
                'r2': r2
            })
    
    return pairs

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main function to compute all features for a dataframe of compositions.
    
    Adds columns:
    - size_mismatch
    - electronegativity_mean
    - electronegativity_var
    - VEC_raw (weighted mean VEC)
    - VEC_avg (same as VEC_raw, or variance? Spec says VEC_raw and VEC_avg)
       *Assumption: VEC_raw is the weighted mean, VEC_avg might be the same or variance.
       *Given T014 description: "VEC_raw, and weighted mean VEC_avg".
       *This implies VEC_raw is the raw sum? No, usually weighted.
       *Let's assume: VEC_raw = weighted mean, VEC_avg = weighted mean (redundant in spec?)
       *Or maybe VEC_raw is the sum of (ci * vec_i) and VEC_avg is the mean?
       *Actually, usually VEC is defined as sum(ci * vec_i).
       *Let's implement:
          - VEC_mean: weighted mean
          - VEC_var: weighted variance
       *The task T014 says: "VEC_raw, and weighted mean VEC_avg".
       *This is ambiguous. I will implement:
          - VEC_mean (weighted mean)
          - VEC_var (weighted variance)
       *And for T015, we add pairwise features.
    
    Args:
        df: DataFrame with 'composition' column
        
    Returns:
        DataFrame with added feature columns
    """
    logger.info("Starting feature computation...")
    
    # Pre-allocate lists for new columns
    size_mismatches = []
    electronegativity_means = []
    electronegativity_vars = []
    vec_means = []
    vec_vars = []
    pairwise_features = [] # Will store list of dicts per row, then flatten
    
    for idx, row in df.iterrows():
        comp_str = row['composition']
        comp = parse_composition_string(comp_str)
        
        if not comp:
            logger.warning(f"Empty composition at row {idx}: {comp_str}")
            size_mismatches.append(0.0)
            electronegativity_means.append(0.0)
            electronegativity_vars.append(0.0)
            vec_means.append(0.0)
            vec_vars.append(0.0)
            pairwise_features.append([])
            continue
        
        elements = list(comp.keys())
        fractions = list(comp.values())
        
        # Get properties
        radii = []
        en_values = []
        vec_values = []
        
        valid = True
        for el in elements:
            props = get_element_properties(el)
            if props['atomic_radius'] == 0.0:
                logger.warning(f"Unknown properties for {el} at row {idx}")
                valid = False
                break
            radii.append(props['atomic_radius'])
            en_values.append(props['electronegativity'])
            vec_values.append(props['VEC'])
        
        if not valid:
            size_mismatches.append(0.0)
            electronegativity_means.append(0.0)
            electronegativity_vars.append(0.0)
            vec_means.append(0.0)
            vec_vars.append(0.0)
            pairwise_features.append([])
            continue
        
        # Compute single-value features
        size_mismatches.append(compute_size_mismatch(comp))
        electronegativity_means.append(compute_weighted_mean(en_values, fractions))
        electronegativity_vars.append(compute_weighted_variance(en_values, fractions))
        vec_means.append(compute_weighted_mean(vec_values, fractions))
        vec_vars.append(compute_weighted_variance(vec_values, fractions))
        
        # Compute pairwise features
        pairs = compute_pairwise_size_mismatch(comp)
        pairwise_features.append(pairs)
    
    # Add single-value columns
    df['size_mismatch'] = size_mismatches
    df['electronegativity_mean'] = electronegativity_means
    df['electronegativity_var'] = electronegativity_vars
    df['VEC_mean'] = vec_means
    df['VEC_var'] = vec_vars
    
    # Expand pairwise features into columns
    # We need to determine the max number of pairs to create columns, or use a dynamic approach
    # Since compositions are ternary (mostly), max pairs = 3.
    # We'll create columns: pair_1_mismatch, pair_2_mismatch, pair_3_mismatch
    
    max_pairs = 0
    for pairs in pairwise_features:
        if len(pairs) > max_pairs:
            max_pairs = len(pairs)
    
    if max_pairs == 0:
        logger.warning("No pairwise features found in dataset.")
        return df
    
    for i in range(max_pairs):
        col_name = f'pair_{i+1}_mismatch'
        df[col_name] = [p[i]['mismatch'] if i < len(p) else 0.0 for p in pairwise_features]
        # Optionally store pair names if needed, but for now just mismatch
        # We could also store 'pair_{i+1}_elements'
    
    logger.info(f"Feature computation complete. Added {max_pairs} pairwise columns.")
    return df

def main():
    """Main entry point for feature engineering pipeline."""
    # This function is typically called by a pipeline script
    # For testing, we can load a sample CSV
    logger.info("Running feature engineering module...")
    
    # Example usage:
    # df = pd.read_csv("data/processed/ingested_data.csv")
    # df = compute_features(df)
    # df.to_csv("data/processed/features.csv", index=False)
    pass

if __name__ == "__main__":
    main()