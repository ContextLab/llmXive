"""
Feature Engineering Module for Elastic Anisotropy Prediction.

Computes compositional descriptors (atomic radius variance, electronegativity std dev,
valence electron concentration) for FCC metal alloys using the mendeleev library.
"""
import sys
import logging
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from mendeleev import element as mendeleev_element

from src.utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

# Constants for feature calculation
MISSING_VALUE = -999.0

def get_element_properties(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch atomic properties for a given element symbol using mendeleev.

    Args:
        symbol: Chemical symbol (e.g., 'Cu', 'Al').

    Returns:
        Dictionary containing atomic_radius (pm), electronegativity (Pauling),
        and valence (number of valence electrons). Returns None if element not found.
    """
    try:
        el = mendeleev_element(symbol)
        # mendeleev properties might be None if not available
        radius = el.atomic_radius
        electronegativity = el.electronegativity
        
        # Determine valence electrons
        # Use group number for main group, or specific valence if available
        # For transition metals, we often use the group number or specific valence
        # Mendeleev 'valence' property can be a list, we take the max or a representative
        valence = None
        if hasattr(el, 'valence') and el.valence:
            if isinstance(el.valence, list):
                valence = max(el.valence)
            else:
                valence = el.valence
        else:
            # Fallback: use group number for main group, or infer from electron config
            # Simple heuristic: group number for groups 1-2, 13-18
            group = el.group_number
            if group:
                if group <= 2:
                    valence = group
                elif group >= 13:
                    valence = group - 10
                else:
                    # Transition metals: often use group number or 2 for simple models
                    # Using group number as a proxy for valence d+s electrons
                    valence = group 
            
        if radius is None or electronegativity is None or valence is None:
            log_warning(f"Missing properties for element {symbol}: r={radius}, chi={electronegativity}, v={valence}")
            return None

        return {
            'symbol': symbol,
            'atomic_radius': float(radius),
            'electronegativity': float(electronegativity),
            'valence': float(valence)
        }
    except Exception as e:
        log_error(f"Failed to fetch properties for element {symbol}: {e}")
        return None

def compute_compositional_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute compositional descriptors for each row in the dataframe.
    
    Expected input columns: 'composition' (string like 'Cu0.5Al0.5' or 'Cu-Al')
    or separate columns for elements and fractions if available.
    Based on T012/T013 context, we assume a 'composition' string or need to parse
    from a standard format. If the dataframe has 'elements' and 'fractions' columns,
    use those. Otherwise, attempt to parse 'composition'.
    
    Features calculated:
    1. atomic_radius_variance: Variance of atomic radii weighted by fraction
    2. electronegativity_std: Standard deviation of electronegativity weighted by fraction
    3. valence_electron_concentration (VEC): Weighted average of valence electrons
    
    Args:
        df: DataFrame containing material data.
        
    Returns:
        DataFrame with added feature columns.
    """
    if df.empty:
        log_info("Empty dataframe provided to feature engineering. Returning empty.")
        return df

    # Ensure we have a column to parse
    if 'composition' not in df.columns:
        # Try to find alternative columns or raise error
        available_cols = list(df.columns)
        raise ValueError(f"Input DataFrame missing 'composition' column. Available: {available_cols}")

    results = []
    skipped_count = 0

    for idx, row in df.iterrows():
        comp_str = row['composition']
        if pd.isna(comp_str) or not isinstance(comp_str, str):
            log_warning(f"Row {idx} has invalid composition: {comp_str}. Skipping.")
            skipped_count += 1
            # Add NaN row
            new_row = row.to_dict()
            new_row['atomic_radius_variance'] = np.nan
            new_row['electronegativity_std'] = np.nan
            new_row['valence_electron_concentration'] = np.nan
            results.append(new_row)
            continue

        # Parse composition string. Expected formats: "Cu0.5Al0.5", "Cu-Al", "Cu", etc.
        # Simple parser for "ElementFraction" format
        elements = []
        fractions = []
        
        # Normalize: replace '-' with nothing or split logic if needed
        # Assuming format like "Cu0.5Al0.5" or "CuAl"
        import re
        # Regex to find Element (Capital + optional lowercase) followed by optional number
        pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
        matches = re.findall(pattern, comp_str)
        
        if not matches:
            log_warning(f"Row {idx}: Could not parse composition '{comp_str}'. Skipping.")
            skipped_count += 1
            new_row = row.to_dict()
            new_row['atomic_radius_variance'] = np.nan
            new_row['electronegativity_std'] = np.nan
            new_row['valence_electron_concentration'] = np.nan
            results.append(new_row)
            continue

        total_fraction = 0.0
        for sym, frac_str in matches:
            if frac_str:
                frac = float(frac_str)
            else:
                frac = 1.0 # If no number, assume 1 (e.g. "CuAl" -> 1:1)
            
            elements.append(sym)
            fractions.append(frac)
            total_fraction += frac

        # Normalize fractions to sum to 1
        if total_fraction == 0:
            log_warning(f"Row {idx}: Zero total fraction in composition '{comp_str}'. Skipping.")
            skipped_count += 1
            new_row = row.to_dict()
            new_row['atomic_radius_variance'] = np.nan
            new_row['electronegativity_std'] = np.nan
            new_row['valence_electron_concentration'] = np.nan
            results.append(new_row)
            continue
        
        fractions = [f / total_fraction for f in fractions]

        # Fetch properties
        props_list = []
        valid = True
        for sym, frac in zip(elements, fractions):
            props = get_element_properties(sym)
            if props is None:
                valid = False
                break
            props_list.append((props, frac))

        if not valid:
            log_warning(f"Row {idx}: Failed to fetch properties for some elements in '{comp_str}'. Skipping.")
            skipped_count += 1
            new_row = row.to_dict()
            new_row['atomic_radius_variance'] = np.nan
            new_row['electronegativity_std'] = np.nan
            new_row['valence_electron_concentration'] = np.nan
            results.append(new_row)
            continue

        # Calculate features
        radii = [p['atomic_radius'] for p, _ in props_list]
        chis = [p['electronegativity'] for p, _ in props_list]
        valences = [p['valence'] for p, _ in props_list]
        fracs = [f for _, f in props_list]

        # Weighted Mean
        mean_radius = np.average(radii, weights=fracs)
        mean_chi = np.average(chis, weights=fracs)
        mean_valence = np.average(valences, weights=fracs)

        # Weighted Variance for Radius: sum(w * (x - mean)^2)
        radius_variance = np.sum(np.array(fracs) * (np.array(radii) - mean_radius) ** 2)

        # Weighted Std Dev for Electronegativity: sqrt(sum(w * (x - mean)^2))
        chi_std = np.sqrt(np.sum(np.array(fracs) * (np.array(chis) - mean_chi) ** 2))

        # VEC is the weighted average
        vec = mean_valence

        new_row = row.to_dict()
        new_row['atomic_radius_variance'] = radius_variance
        new_row['electronegativity_std'] = chi_std
        new_row['valence_electron_concentration'] = vec
        results.append(new_row)

    log_info(f"Feature engineering complete. Processed {len(df) - skipped_count} rows, skipped {skipped_count}.")
    return pd.DataFrame(results)

def main():
    """
    Main entry point for running feature engineering on the cleaned dataset.
    Expects cleaned data at data/processed/elastic_anisotropy_cleaned.csv (or similar).
    Outputs to data/processed/elastic_anisotropy_features.csv.
    """
    from src.utils.config import get_path
    
    # Determine input/output paths
    # Assuming T013 output is the input for T014
    input_path = get_path("data_processed", "elastic_anisotropy_cleaned.csv")
    output_path = get_path("data_processed", "elastic_anisotropy_features.csv")

    if not Path(input_path).exists():
        log_error(f"Input file not found: {input_path}")
        sys.exit(1)

    log_info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        log_error(f"Failed to load input data: {e}")
        sys.exit(1)

    log_info(f"Loaded {len(df)} rows. Computing features...")
    df_features = compute_compositional_features(df)

    log_info(f"Saving results to {output_path}")
    try:
        df_features.to_csv(output_path, index=False)
        log_success(f"Features saved to {output_path}")
    except Exception as e:
        log_error(f"Failed to save output data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
