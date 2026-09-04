import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from mendeleev import element

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """Fetch atomic properties for a given element symbol."""
    try:
        el = element(symbol)
        return {
            'atomic_radius': el.atomic_radius,
            'electronegativity': el.electronegativity,
            'atomic_number': el.atomic_number,
            'atomic_weight': el.atomic_weight
        }
    except Exception as e:
        logger.warning(f"Could not fetch properties for element {symbol}: {e}")
        return {
            'atomic_radius': None,
            'electronegativity': None,
            'atomic_number': None,
            'atomic_weight': None
        }

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Fe50Ni30Co20' into a dict {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}.
    Handles standard chemical notation where numbers are percentages.
    """
    import re
    composition_str = composition_str.replace(" ", "")
    # Pattern to match Element symbol followed by optional number
    pattern = r'([A-Z][a-z]?)(\d+(?:\.\d+)?)'
    matches = re.findall(pattern, composition_str)
    
    result = {}
    total = 0.0
    for symbol, value in matches:
        val = float(value)
        result[symbol] = val
        total += val
    
    # Normalize to fractions if sum is not 100 (handle cases where sum might be slightly off or unitless)
    if total > 1.0:
        for k in result:
            result[k] /= total
    elif total == 0:
        # Fallback for bad data, though shouldn't happen with valid input
        logger.warning(f"Total composition sum is 0 for {composition_str}")
    
    return result

def calculate_weighted_mean_radius(composition: Dict[str, float]) -> Optional[float]:
    """Calculate the weighted mean atomic radius."""
    if not composition:
        return None
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        radius = props.get('atomic_radius')
        if radius is not None:
            weighted_sum += radius * fraction
            total_weight += fraction
    
    if total_weight == 0:
        return None
    
    return weighted_sum / total_weight

def calculate_radius_mismatch(composition: Dict[str, float]) -> Optional[float]:
    """
    Calculate radius mismatch delta_r = sqrt( sum( c_i * (1 - r_i / r_bar)^2 ) )
    where r_bar is the weighted mean radius.
    """
    r_bar = calculate_weighted_mean_radius(composition)
    if r_bar is None or r_bar == 0:
        return None
    
    sum_sq = 0.0
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        r_i = props.get('atomic_radius')
        if r_i is not None:
            term = (1 - r_i / r_bar) ** 2
            sum_sq += fraction * term
    
    return np.sqrt(sum_sq)

def calculate_electronegativity_difference(composition: Dict[str, float]) -> Optional[float]:
    """
    Calculate electronegativity difference delta_chi = sqrt( sum( c_i * c_j * (chi_i - chi_j)^2 ) )
    Simplified: variance of electronegativity weighted by composition.
    """
    if not composition:
        return None
    
    chi_values = []
    weights = []
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        chi = props.get('electronegativity')
        if chi is not None:
            chi_values.append(chi)
            weights.append(fraction)
    
    if not chi_values:
        return None
    
    chi_array = np.array(chi_values)
    weights_array = np.array(weights)
    
    # Weighted mean
    chi_bar = np.average(chi_array, weights=weights_array)
    
    # Weighted variance (approximate delta_chi)
    # Using formula: sqrt( sum( c_i * (chi_i - chi_bar)^2 ) )
    variance = np.sum(weights_array * (chi_array - chi_bar) ** 2)
    
    return np.sqrt(variance)

def calculate_vec(composition: Dict[str, float]) -> Optional[float]:
    """Calculate Valence Electron Concentration (VEC)."""
    if not composition:
        return None
    
    vec_sum = 0.0
    total_weight = 0.0
    
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        # Mendeleev doesn't always have a direct 'valence' attribute that is standard.
        # We will approximate using group number or atomic number if group is missing.
        # For metallic glasses, VEC is often calculated based on group number.
        # Mendeleev element object has 'group' attribute.
        el = element(symbol)
        group = el.group
        
        if group is None:
            # Fallback: if group is missing, we might need to hardcode or skip.
            # For this implementation, we'll try to use the group number if available.
            # If not, we skip this element or use a default.
            logger.warning(f"Group number missing for {symbol}, skipping in VEC calc")
            continue
        
        # Some groups are tuples (e.g. (8, 9, 10) for Fe, Co, Ni in some periodic tables)
        # We take the first one or average if needed. Usually VEC uses the group number directly.
        if isinstance(group, tuple):
            valence = group[0]
        else:
            valence = group
        
        vec_sum += valence * fraction
        total_weight += fraction
    
    if total_weight == 0:
        return None
    
    return vec_sum / total_weight

def compute_descriptors(composition_str: str) -> Dict[str, Optional[float]]:
    """Compute all descriptors for a single composition string."""
    composition = parse_composition(composition_str)
    
    radius_mismatch = calculate_radius_mismatch(composition)
    electronegativity_diff = calculate_electronegativity_difference(composition)
    vec = calculate_vec(composition)
    
    # Weighted mean radius is for diagnostic only (T021), but we compute it here for completeness
    # if needed for other tasks, though T026 only requires the three main ones.
    
    return {
        'radius_mismatch': radius_mismatch,
        'electronegativity_diff': electronegativity_diff,
        'VEC': vec
    }

def process_dataframe(df: pd.DataFrame, composition_col: str = 'composition', target_col: str = 'Tg') -> pd.DataFrame:
    """
    Process a dataframe to add descriptor columns.
    """
    logger.info(f"Processing {len(df)} rows for descriptors...")
    
    descriptors = []
    valid_count = 0
    invalid_count = 0
    
    for idx, row in df.iterrows():
        comp_str = str(row.get(composition_col, ''))
        if not comp_str or comp_str == 'nan':
            descriptors.append({
                'radius_mismatch': None,
                'electronegativity_diff': None,
                'VEC': None
            })
            invalid_count += 1
            continue
        
        try:
            desc = compute_descriptors(comp_str)
            descriptors.append(desc)
            if desc['radius_mismatch'] is not None:
                valid_count += 1
            else:
                invalid_count += 1
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            descriptors.append({
                'radius_mismatch': None,
                'electronegativity_diff': None,
                'VEC': None
            })
            invalid_count += 1
    
    desc_df = pd.DataFrame(descriptors)
    result_df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    
    logger.info(f"Descriptor computation complete. Valid: {valid_count}, Invalid: {invalid_count}")
    return result_df

def save_diagnostic_log(weighted_mean_radius: Optional[float], output_path: Path) -> None:
    """Save diagnostic log for weighted mean radius (T021)."""
    log_data = {
        'weighted_mean_radius': weighted_mean_radius
    }
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Diagnostic log saved to {output_path}")

def save_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """Save the computed descriptors to a CSV file."""
    required_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC']
    
    # Ensure we only save the relevant columns plus any necessary IDs if needed
    # The task verification specifically checks for these columns.
    # We assume the dataframe already has these columns after process_dataframe.
    
    cols_to_save = [c for c in required_cols if c in df.columns]
    if not cols_to_save:
        raise ValueError(f"None of the required columns {required_cols} found in dataframe.")
    
    output_df = df[cols_to_save]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved to {output_path}")

def main():
    """Main entry point to run the descriptor computation pipeline."""
    project_root = get_project_root()
    input_path = project_root / 'data' / 'processed' / 'cleaned_mg.csv'
    output_path = project_root / 'data' / 'processed' / 'descriptors.csv'
    diagnostic_path = project_root / 'data' / 'processed' / 'diagnostic_log.json'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load cleaned data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Check for composition column
    if 'composition' not in df.columns:
        logger.error("Input file must contain 'composition' column")
        sys.exit(1)
    
    # Compute descriptors
    df_with_desc = process_dataframe(df)
    
    # Save diagnostic log (T021) - calculate weighted mean radius for the whole dataset if needed
    # The task T021 asks for 'weighted mean radius' for diagnostic logging.
    # We can calculate the average of the weighted mean radii of all samples.
    wmr_values = []
    for _, row in df_with_desc.iterrows():
        # Re-calculate or store if we had stored it. Since we didn't store it in the main DF yet,
        # we compute it on the fly for the diagnostic.
        comp_str = str(row['composition'])
        if comp_str and comp_str != 'nan':
            comp_dict = parse_composition(comp_str)
            wmr = calculate_weighted_mean_radius(comp_dict)
            if wmr is not None:
                wmr_values.append(wmr)
    
    avg_wmr = np.mean(wmr_values) if wmr_values else None
    save_diagnostic_log(avg_wmr, diagnostic_path)
    
    # Save descriptors (T026)
    save_descriptors(df_with_desc, output_path)
    
    logger.info("Pipeline completed successfully.")

if __name__ == '__main__':
    main()
