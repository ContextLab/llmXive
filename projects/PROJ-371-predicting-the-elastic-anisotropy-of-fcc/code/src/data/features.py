"""
Feature engineering module for computing compositional descriptors.

Computes atomic radius variance, electronegativity standard deviation,
and valence electron concentration (VEC) for FCC alloys using mendeleev.
"""
import sys
import logging
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from mendeleev import element as mendeleev_element

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Mendeleev property names mapping to standard descriptors
# We use covalent radius for atomic size, Pauling scale for electronegativity
# and group number (valence electrons) for VEC.
PROP_ATOMIC_RADIUS = "covalent_radius_pyy"
PROP_ELECTRONEGATIVITY = "electronegativity"
PROP_VALENCE_ELECTRONS = "group"  # Mendeleev group number corresponds to valence for main group; transition metals need adjustment

def _get_valence_electrons(symbol: str) -> int:
    """
    Determine valence electron count for an element.
    For transition metals (d-block), we use the number of s + d electrons.
    For main group, we use group number logic or s+p count.
    Mendeleev's 'group' attribute is 1-18.
    """
    try:
        el = mendeleev_element(symbol)
        # Mendeleev 'group' is 1-18.
        # For VEC in alloys, we typically count outer shell electrons.
        # Transition metals (groups 3-12): usually valence = group - 10 + 2 (s) ?
        # Actually, standard practice for VEC in HEAs: sum of (s+d) electrons.
        # Mendeleev has 'electron_configuration'. Let's parse it or use a heuristic.
        # Simpler: use the 'valence_electrons' property if available, else compute.
        if hasattr(el, 'valence_electrons') and el.valence_electrons is not None:
            return int(el.valence_electrons)
        
        # Fallback: use group number logic for common cases
        group = el.group
        if group is None:
            # Unknown, default to 1
            return 1
        
        if 1 <= group <= 2:
            return group
        elif 3 <= group <= 12:
            # Transition metals: usually group number - 10 + 2 (s) ?
            # Actually, VEC for transition metals is often taken as group number - 10 (d) + 2 (s) = group - 8?
            # Let's check standard VEC definitions: Sc (3) -> 3, Ti (4) -> 4, V (5) -> 5, Cr (6) -> 6, Mn (7) -> 7, Fe (8) -> 8, Co (9) -> 9, Ni (10) -> 10, Cu (11) -> 11, Zn (12) -> 12.
            # Wait, for VEC in HEAs, Cu is often 11, Zn is 12.
            # So for transition metals, VEC = group number - 10 + 2? No.
            # Let's just use the group number directly for 1-2, and for 3-12, it's often group number.
            # But Zn (12) has full d10 s2 -> 2 valence? No, in alloys it's 12?
            # Standard VEC calculation in literature: sum of (ns + (n-1)d) electrons.
            # Mendeleev 'group' for Zn is 12. Valence is 2.
            # Let's try to get electron config.
            try:
                config = el.electron_configuration
                # This is a string like '1s2 2s2 2p6 3s2 3p6 3d10 4s1'
                # We need to sum s and d electrons in the outermost shells?
                # This is complex. Let's use a simpler heuristic based on group.
                # For 3-12: VEC = group - 10 + 2? No.
                # Let's use a lookup for common transition metals if needed.
                # Actually, many papers use: VEC = sum(valence) where valence is s+d.
                # For Fe (group 8): 8 valence? Yes.
                # For Ni (group 10): 10 valence? Yes.
                # For Cu (group 11): 11 valence? Yes.
                # For Zn (group 12): 12 valence? No, Zn is 2.
                # So groups 3-11 are group number. Group 12 is 2?
                if group <= 11:
                    return group
                else:
                    # Group 12 (Zn, Cd, Hg): 2 valence electrons (s2)
                    return 2
            except Exception:
                return group
        elif 13 <= group <= 18:
            # Main group: group - 10
            return group - 10
        else:
            return 1
    except Exception as e:
        logger.warning(f"Could not determine valence electrons for {symbol}: {e}")
        return 1

def get_element_properties(symbol: str) -> Dict[str, float]:
    """
    Fetch atomic properties for a single element symbol.
    
    Args:
        symbol: Element symbol (e.g., 'Fe', 'Ni')
        
    Returns:
        Dictionary with 'radius', 'electronegativity', 'valence_electrons'
        
    Raises:
        ValueError: If element symbol is invalid or properties missing
    """
    symbol = symbol.strip().title()
    try:
        el = mendeleev_element(symbol)
    except Exception as e:
        raise ValueError(f"Invalid element symbol '{symbol}': {e}")

    radius = el.covalent_radius_pyy
    if radius is None:
        radius = el.covalent_radius  # Fallback
    
    if radius is None:
        raise ValueError(f"Missing covalent radius for {symbol}")

    electroneg = el.electronegativity
    if electroneg is None:
        raise ValueError(f"Missing electronegativity for {symbol}")

    valence = _get_valence_electrons(symbol)

    return {
        "radius": float(radius),
        "electronegativity": float(electroneg),
        "valence_electrons": float(valence)
    }

def compute_compositional_features(
    df: pd.DataFrame,
    composition_col: str = "composition",
    atomic_fraction_col: str = "atomic_fractions"
) -> pd.DataFrame:
    """
    Compute compositional features for a DataFrame of alloys.
    
    Features computed:
    - radius_variance: Variance of atomic radii weighted by atomic fraction
    - electronegativity_std: Standard deviation of electronegativity weighted by atomic fraction
    - vec: Valence electron concentration (weighted average)
    
    Args:
        df: DataFrame with 'composition' (list of symbols) and 'atomic_fractions' (list of floats)
        composition_col: Name of column containing list of element symbols
        atomic_fraction_col: Name of column containing list of atomic fractions
        
    Returns:
        DataFrame with original columns plus new feature columns
    """
    if composition_col not in df.columns or atomic_fraction_col not in df.columns:
        raise ValueError(f"Columns '{composition_col}' and '{atomic_fraction_col}' required in input DataFrame")

    results = []
    total_processed = 0
    total_skipped = 0

    for idx, row in df.iterrows():
        try:
            symbols = row[composition_col]
            fractions = row[atomic_fraction_col]
            
            if not isinstance(symbols, list) or not isinstance(fractions, list):
                logger.warning(f"Row {idx}: Invalid composition or fractions format, skipping.")
                total_skipped += 1
                continue
            
            if len(symbols) != len(fractions):
                logger.warning(f"Row {idx}: Mismatched lengths in composition ({len(symbols)}) and fractions ({len(fractions)}), skipping.")
                total_skipped += 1
                continue
            
            # Normalize fractions
            total_frac = sum(fractions)
            if total_frac == 0:
                logger.warning(f"Row {idx}: Zero total atomic fraction, skipping.")
                total_skipped += 1
                continue
            
            fractions = [f / total_frac for f in fractions]
            
            # Fetch properties for each element
            props_list = []
            for sym, frac in zip(symbols, fractions):
                try:
                    props = get_element_properties(sym)
                    props['fraction'] = frac
                    props_list.append(props)
                except ValueError as e:
                    logger.warning(f"Row {idx}: Skipping element {sym} due to {e}")
                    # Skip this element? Or fail the row?
                    # For robustness, we skip the element and recalculate with remaining
                    pass
            
            if not props_list:
                logger.warning(f"Row {idx}: No valid elements found, skipping row.")
                total_skipped += 1
                continue
            
            # Compute weighted mean and variance
            radii = [p['radius'] for p in props_list]
            fracs = [p['fraction'] for p in props_list]
            en_vals = [p['electronegativity'] for p in props_list]
            vec_vals = [p['valence_electrons'] for p in props_list]
            
            # Weighted mean
            mean_radius = sum(r * f for r, f in zip(radii, fracs))
            mean_en = sum(e * f for e, f in zip(en_vals, fracs))
            mean_vec = sum(v * f for v, f in zip(vec_vals, fracs))
            
            # Weighted variance for radius
            variance_radius = sum(f * (r - mean_radius) ** 2 for r, f in zip(radii, fracs))
            
            # Weighted std for electronegativity (population std)
            variance_en = sum(f * (e - mean_en) ** 2 for e, f in zip(en_vals, fracs))
            std_en = np.sqrt(variance_en)
            
            results.append({
                "radius_variance": variance_radius,
                "electronegativity_std": std_en,
                "vec": mean_vec
            })
            total_processed += 1
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            total_skipped += 1

    logger.info(f"Feature computation complete. Processed: {total_processed}, Skipped: {total_skipped}")
    
    if not results:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=["radius_variance", "electronegativity_std", "vec"])
    
    features_df = pd.DataFrame(results)
    return features_df

def main():
    """
    CLI entry point for feature computation.
    Expects a cleaned CSV with 'composition' and 'atomic_fractions' columns.
    """
    import argparse
    from pathlib import Path
    from src.utils.config import get_path
    
    parser = argparse.ArgumentParser(description="Compute compositional features")
    parser.add_argument("--input", type=str, default=None, help="Input CSV path (default: data/processed/elastic_anisotropy_cleaned.csv)")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path (default: data/processed/elastic_anisotropy_features.csv)")
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else get_path("data_processed") / "elastic_anisotropy_cleaned.csv"
    output_path = Path(args.output) if args.output else get_path("data_processed") / "elastic_anisotropy_features.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Check if we need to parse composition strings or if they are already lists
    # Assuming the cleaned data has a 'composition' column with comma-separated strings or lists
    # If it's a string like "Fe,Ni,Cr", we need to split.
    # If it's already a list (from JSON), we use it.
    if 'composition' in df.columns:
        if isinstance(df['composition'].iloc[0], str):
            df['composition'] = df['composition'].apply(lambda x: [s.strip() for s in x.split(',') if s.strip()])
    
    if 'atomic_fractions' in df.columns:
        if isinstance(df['atomic_fractions'].iloc[0], str):
            # Try to parse as JSON list or comma-separated
            import json
            try:
                df['atomic_fractions'] = df['atomic_fractions'].apply(json.loads)
            except json.JSONDecodeError:
                df['atomic_fractions'] = df['atomic_fractions'].apply(lambda x: [float(v) for v in x.split(',') if v.strip()])
    
    features = compute_compositional_features(df)
    
    # Merge features back into the original dataframe
    result_df = pd.concat([df.reset_index(drop=True), features.reset_index(drop=True)], axis=1)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Features saved to {output_path}")

if __name__ == "__main__":
    main()
