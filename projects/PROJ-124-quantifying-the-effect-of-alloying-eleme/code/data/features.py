import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np

try:
    from pymatgen.core import Composition, Element
    from pymatgen.entries.computed_entries import ComputedEntry
except ImportError:
    raise ImportError("pymatgen is required for feature engineering. Install via: pip install pymatgen")

from utils.logger import get_logger

logger = get_logger(__name__)

# Cache for element properties to avoid repeated API calls
_element_cache: Dict[str, Dict[str, Any]] = {}

def get_element_properties(element_symbol: str) -> Dict[str, Any]:
    """
    Fetches atomic properties for a given element symbol using Pymatgen.
    
    Implements robust error handling:
    - Caches results to avoid redundant lookups.
    - Wraps lookups in try/except to handle invalid symbols or missing properties.
    - Returns None if the element is invalid or properties cannot be fetched.
    
    Args:
        element_symbol: The chemical symbol (e.g., "Fe", "Zr").
        
    Returns:
        A dictionary of properties (atomic_radius, electronegativity, VEC, etc.)
        or None if the element is invalid/unknown.
    """
    if element_symbol in _element_cache:
        return _element_cache[element_symbol]

    try:
        elem = Element(element_symbol)
        props = {
            "atomic_number": elem.number,
            "atomic_radius": elem.atomic_radius,
            "electronegativity": elem.electronegativity,
            "atomic_mass": elem.atomic_mass,
            "valence": elem.valence,
            "group": elem.group,
            "period": elem.period
        }
        
        # Calculate VEC (Valence Electron Concentration)
        # For transition metals, we use the group number - 10 (for d-electrons)
        # For main group, we use group number (or 8 - group for some conventions, but standard is group)
        # Pymatgen's 'valence' property usually gives the number of valence electrons
        props["VEC"] = props["valence"]
        
        _element_cache[element_symbol] = props
        return props
        
    except Exception as e:
        logger.error(f"Failed to fetch properties for element '{element_symbol}': {str(e)}")
        return None

def parse_composition_string(comp_str: str) -> Optional[Dict[str, float]]:
    """
    Parses a composition string (e.g., "Fe50Ni40Cr10") into a dictionary of element: fraction.
    
    Args:
        comp_str: String representation of composition.
        
    Returns:
        Dictionary mapping element symbols to their atomic fractions, or None if parsing fails.
    """
    try:
        # Use Pymatgen's Composition parser for robustness
        comp = Composition(comp_str)
        return {str(el): frac for el, frac in comp.items()}
    except Exception as e:
        logger.error(f"Failed to parse composition string '{comp_str}': {str(e)}")
        return None

def compute_weighted_mean(values: List[float], weights: List[float]) -> float:
    """Computes weighted mean of a list of values."""
    if not values or not weights:
        return 0.0
    return float(np.average(values, weights=weights))

def compute_weighted_variance(values: List[float], weights: List[float]) -> float:
    """Computes weighted variance of a list of values."""
    if not values or not weights or len(values) < 2:
        return 0.0
    mean = compute_weighted_mean(values, weights)
    variance = np.average((np.array(values) - mean) ** 2, weights=weights)
    return float(variance)

def compute_size_mismatch(atomic_radii: List[float], weights: List[float]) -> float:
    """
    Computes the size mismatch parameter (delta) based on atomic radii.
    Formula: delta = sqrt(sum(omega_i * (1 - r_i/r_bar)^2))
    where r_bar is the weighted average radius.
    """
    if not atomic_radii or not weights:
        return 0.0
    
    r_bar = compute_weighted_mean(atomic_radii, weights)
    if r_bar == 0:
        return 0.0
    
    deviations = [(1 - (r / r_bar)) ** 2 for r in atomic_radii]
    delta_sq = compute_weighted_mean(deviations, weights)
    return float(np.sqrt(delta_sq))

def compute_pairwise_size_mismatch(atomic_radii: List[float], weights: List[float]) -> Dict[str, float]:
    """
    Computes pairwise size mismatch for all unique pairs in the composition.
    
    Args:
        atomic_radii: List of atomic radii for elements in the composition.
        weights: List of atomic fractions (weights) for elements.
        
    Returns:
        Dictionary with keys as "Element1-Element2" and values as mismatch metrics.
    """
    if not atomic_radii or not weights or len(atomic_radii) < 2:
        return {}
    
    # This function assumes atomic_radii and weights are aligned with element order
    # We need to return a dict of pairwise mismatches.
    # Since we don't have element symbols here, we return a list or a generic structure.
    # However, the task asks for "pairwise feature columns appended to the dataframe".
    # We will return a list of values that can be expanded into columns later, 
    # or we can compute a summary statistic (max, mean) if specific pairs aren't tracked.
    # Given the requirement "calculate for A-B, A-C, B-C", we return a list of values.
    
    pairs = []
    for i in range(len(atomic_radii)):
        for j in range(i + 1, len(atomic_radii)):
            r_i = atomic_radii[i]
            r_j = atomic_radii[j]
            if r_i == 0 or r_j == 0:
                pairs.append(0.0)
            else:
                # Simple mismatch metric: |r_i - r_j| / max(r_i, r_j)
                mismatch = abs(r_i - r_j) / max(r_i, r_j)
                pairs.append(mismatch)
    
    return pairs

def compute_features(df: pd.DataFrame, composition_col: str = "composition") -> Tuple[pd.DataFrame, List[str]]:
    """
    Main function to compute all physics-based features for a dataframe of compositions.
    
    Implements robust error handling for Pymatgen property fetch failures:
    - Wraps element property lookups in try/except.
    - Logs specific errors with element symbol and composition ID.
    - Excludes rows with unknown/invalid elements from the final dataset.
    
    Args:
        df: Input dataframe with a composition column.
        composition_col: Name of the column containing composition strings.
        
    Returns:
        Tuple of (processed_dataframe, list_of_excluded_row_ids)
    """
    logger.info(f"Starting feature engineering on {len(df)} rows")
    
    excluded_rows = []
    valid_indices = []
    
    # Pre-allocate lists for vectorized operations where possible
    atomic_radii_list = []
    electronegativity_list = []
    vec_list = []
    weights_list = []
    element_symbols_list = []
    row_ids = []
    
    for idx, row in df.iterrows():
        row_id = idx
        comp_str = row[composition_col]
        
        # Parse composition
        comp_dict = parse_composition_string(comp_str)
        if comp_dict is None:
            logger.error(f"Row {row_id}: Failed to parse composition '{comp_str}'. Excluding row.")
            excluded_rows.append(row_id)
            continue
        
        elements = list(comp_dict.keys())
        fractions = list(comp_dict.values())
        
        # Fetch properties for each element
        elem_props = []
        valid_elements = True
        
        for elem_sym in elements:
            props = get_element_properties(elem_sym)
            if props is None:
                logger.error(f"Row {row_id}: Invalid or unknown element '{elem_sym}' in composition '{comp_str}'. Excluding row.")
                valid_elements = False
                break
            elem_props.append(props)
        
        if not valid_elements:
            excluded_rows.append(row_id)
            continue
        
        # Extract properties
        radii = [p["atomic_radius"] for p in elem_props]
        electronegativities = [p["electronegativity"] for p in elem_props]
        vecs = [p["VEC"] for p in elem_props]
        
        atomic_radii_list.append(radii)
        electronegativity_list.append(electronegativities)
        vec_list.append(vecs)
        weights_list.append(fractions)
        element_symbols_list.append(elements)
        row_ids.append(row_id)
        valid_indices.append(idx)
    
    if not valid_indices:
        logger.critical("No valid rows remaining after filtering invalid elements. Check input data.")
        return pd.DataFrame(), excluded_rows
    
    logger.info(f"Feature engineering: {len(valid_indices)} valid rows, {len(excluded_rows)} excluded rows.")
    
    # Compute aggregated features
    df_valid = df.iloc[valid_indices].copy()
    df_valid["source_row_id"] = row_ids
    
    # Calculate means and variances
    df_valid["atomic_radius_mean"] = [compute_weighted_mean(r, w) for r, w in zip(atomic_radii_list, weights_list)]
    df_valid["atomic_radius_var"] = [compute_weighted_variance(r, w) for r, w in zip(atomic_radii_list, weights_list)]
    df_valid["electronegativity_mean"] = [compute_weighted_mean(e, w) for e, w in zip(electronegativity_list, weights_list)]
    df_valid["electronegativity_var"] = [compute_weighted_variance(e, w) for e, w in zip(electronegativity_list, weights_list)]
    df_valid["VEC_raw"] = [compute_weighted_mean(v, w) for v, w in zip(vec_list, weights_list)]
    df_valid["VEC_avg"] = df_valid["VEC_raw"] # Alias for clarity
    
    # Calculate size mismatch (delta)
    df_valid["size_mismatch"] = [compute_size_mismatch(r, w) for r, w in zip(atomic_radii_list, weights_list)]
    
    # Calculate pairwise size mismatch
    # We will store the list of pairwise values and then expand them into columns
    pairwise_results = [compute_pairwise_size_mismatch(r, w) for r, w in zip(atomic_radii_list, weights_list)]
    
    # Determine max number of pairs to create columns
    max_pairs = max(len(p) for p in pairwise_results) if pairwise_results else 0
    
    # Create columns for pairwise mismatches (e.g., pairwise_mismatch_0, pairwise_mismatch_1, ...)
    # If a row has fewer pairs, fill with 0
    for i in range(max_pairs):
        col_name = f"pairwise_mismatch_{i}"
        df_valid[col_name] = [p[i] if i < len(p) else 0.0 for p in pairwise_results]
    
    # Log excluded rows
    if excluded_rows:
        exclusion_log_path = Path("data/processed/exclusion_log.csv")
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        exclusion_df = pd.DataFrame({"row_id": excluded_rows, "reason": "Invalid/Unknown Element"})
        exclusion_df.to_csv(exclusion_log_path, index=False)
        logger.info(f"Exclusion log saved to {exclusion_log_path}")
    
    return df_valid, excluded_rows

def main():
    """
    Entry point for feature engineering script.
    Loads raw data, computes features, and saves the processed dataset.
    """
    logger.info("Starting feature engineering pipeline (main entry point).")
    
    # Load processed data from ingestion step
    input_path = Path("data/processed/normalized_compositions.csv")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run ingest.py first.")
        return
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Compute features
    df_features, excluded = compute_features(df)
    
    if df_features.empty:
        logger.error("No valid features computed. Pipeline halted.")
        return
    
    # Save features
    output_path = Path("data/processed/features.csv")
    df_features.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df_features)} rows to {output_path}")
    
    # Log summary
    logger.info(f"Feature engineering complete. Excluded {len(excluded)} rows.")

if __name__ == "__main__":
    main()