import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from mendeleev import element

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """
    Retrieve atomic properties for a given element symbol using mendeleev.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu')
        
    Returns:
        Dictionary containing atomic radius, electronegativity, valence electrons, etc.
        
    Raises:
        ValueError: If element is not found or invalid symbol
    """
    try:
        el = element(symbol)
        return {
            'symbol': el.symbol,
            'atomic_radius': el.atomic_radius,  # in pm
            'electronegativity': el.electronegativity,  # Pauling scale
            'valence_electrons': el.valence_electrons,
            'atomic_number': el.atomic_number,
            'mass': el.mass
        }
    except Exception as e:
        raise ValueError(f"Could not retrieve properties for element '{symbol}': {e}")

def calculate_weighted_mean_radius(composition: Dict[str, float]) -> float:
    """
    Calculate the weighted mean atomic radius based on stoichiometry.
    
    Args:
        composition: Dict mapping element symbols to atomic fractions (summing to 1.0)
        
    Returns:
        Weighted mean radius in pm
    """
    total_radius = 0.0
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        total_radius += props['atomic_radius'] * fraction
    return total_radius

def calculate_radius_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate radius mismatch parameter (delta) for metallic glasses.
    
    Formula: delta = sqrt( sum( c_i * (1 - r_i/r_bar)^2 ) )
    where r_bar is the weighted mean radius.
    
    Args:
        composition: Dict mapping element symbols to atomic fractions
        
    Returns:
        Radius mismatch parameter (dimensionless)
    """
    r_bar = calculate_weighted_mean_radius(composition)
    if r_bar == 0:
        return 0.0
    
    sum_sq = 0.0
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        r_i = props['atomic_radius']
        sum_sq += fraction * ((1 - (r_i / r_bar)) ** 2)
    
    return np.sqrt(sum_sq)

def calculate_electronegativity_difference(composition: Dict[str, float]) -> float:
    """
    Calculate the electronegativity difference (delta_chi) for the alloy.
    
    Formula: delta_chi = sqrt( sum( c_i * (chi_i - chi_bar)^2 ) )
    where chi_bar is the weighted mean electronegativity.
    
    Args:
        composition: Dict mapping element symbols to atomic fractions
        
    Returns:
        Electronegativity difference (Pauling scale)
    """
    chi_bar = 0.0
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        chi_bar += props['electronegativity'] * fraction
    
    sum_sq = 0.0
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        chi_i = props['electronegativity']
        sum_sq += fraction * ((chi_i - chi_bar) ** 2)
    
    return np.sqrt(sum_sq)

def calculate_vec(composition: Dict[str, float]) -> float:
    """
    Calculate the average Valence Electron Concentration (VEC).
    
    Formula: VEC = sum( c_i * VEC_i )
    
    Args:
        composition: Dict mapping element symbols to atomic fractions
        
    Returns:
        Average VEC (electrons/atom)
    """
    vec_sum = 0.0
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        # Handle cases where valence_electrons might be None or 0
        valence = props['valence_electrons'] if props['valence_electrons'] is not None else 0
        vec_sum += valence * fraction
    return vec_sum

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Zr50Cu40Al10' or 'Zr50.0Cu40.0Al10.0'
    into a dictionary of element -> fraction.
    
    Args:
        composition_str: String representation of composition
        
    Returns:
        Dict mapping element symbols to atomic fractions (normalized to 1.0)
    """
    import re
    
    # Pattern to match element symbol followed by optional number
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        raise ValueError(f"Could not parse composition string: {composition_str}")
    
    composition = {}
    total = 0.0
    
    for symbol, amount in matches:
        amount = float(amount)
        composition[symbol] = amount
        total += amount
    
    # Normalize to fractions
    if total == 0:
        raise ValueError(f"Total composition is zero for: {composition_str}")
    
    return {k: v / total for k, v in composition.items()}

def compute_descriptors(row: pd.Series) -> Dict[str, float]:
    """
    Compute all descriptors for a single row of data.
    
    Args:
        row: A pandas Series containing 'composition' and optionally 'Tg'
        
    Returns:
        Dictionary of computed descriptors
    """
    comp_str = row.get('composition')
    if pd.isna(comp_str) or not isinstance(comp_str, str):
        raise ValueError(f"Invalid composition: {comp_str}")
    
    try:
        composition = parse_composition(comp_str)
    except ValueError as e:
        raise ValueError(f"Failed to parse composition '{comp_str}': {e}")
    
    descriptors = {
        'radius_mismatch': calculate_radius_mismatch(composition),
        'electronegativity_diff': calculate_electronegativity_difference(composition),
        'vec': calculate_vec(composition),
        'weighted_mean_radius': calculate_weighted_mean_radius(composition)
    }
    
    # Add composition fractions as features (optional, depending on needs)
    # For now, we stick to the aggregate descriptors as per task T020/T021
    
    return descriptors

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a dataframe to add descriptor columns.
    
    Args:
        df: Input dataframe with 'composition' column
        
    Returns:
        DataFrame with added descriptor columns
    """
    logger.info(f"Processing {len(df)} rows to compute descriptors...")
    
    results = []
    for idx, row in df.iterrows():
        try:
            desc = compute_descriptors(row)
            desc['composition'] = row['composition']
            if 'Tg' in row and not pd.isna(row['Tg']):
                desc['Tg'] = row['Tg']
            results.append(desc)
        except Exception as e:
            logger.warning(f"Skipping row {idx} due to error: {e}")
            continue
    
    if not results:
        raise ValueError("No valid rows processed. Check composition column format.")
    
    result_df = pd.DataFrame(results)
    logger.info(f"Successfully processed {len(result_df)} rows.")
    return result_df

def save_descriptors(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the computed descriptors to a CSV file.
    
    Args:
        df: DataFrame containing descriptors
        output_path: Path to save the CSV file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Descriptors saved to {output_path}")

def main():
    """
    Main entry point to load cleaned data, compute descriptors, and save them.
    """
    # Define paths based on project structure
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "processed" / "cleaned_mg.csv"
    output_path = project_root / "data" / "processed" / "descriptors.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T014 (cleaning) has been completed and cleaned_mg.csv exists.")
        sys.exit(1)
    
    # Load cleaned data
    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'composition' not in df.columns:
        logger.error("Input data must contain a 'composition' column.")
        sys.exit(1)
    
    # Compute descriptors
    descriptors_df = process_dataframe(df)
    
    # Save to CSV
    save_descriptors(descriptors_df, str(output_path))
    
    logger.info("Task T026 completed successfully.")

if __name__ == "__main__":
    main()