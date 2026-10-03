import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np

# Attempt to import mendeleev for element properties
try:
    from mendeleev import element
except ImportError:
    # If mendeleev is not installed, we cannot compute descriptors
    # This will cause the script to fail loudly as required
    raise ImportError("mendeleev is required for descriptor calculation. Install with: pip install mendeleev==0.31.0")

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while not (current / ".git").exists():
        current = current.parent
        if current == current.parent:
            raise RuntimeError("Could not find project root")
    return current

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """
    Get atomic properties for a given element symbol.
    
    Args:
        symbol: Element symbol (e.g., 'Fe', 'Zr')
        
    Returns:
        Dictionary with atomic radius (pm), electronegativity (Pauling), 
        and valence electrons.
        
    Raises:
        ValueError: If element symbol is invalid
    """
    try:
        elem = element(symbol)
        return {
            'radius': elem.atomic_radius,  # in pm
            'electronegativity': elem.electronegativity,  # Pauling
            'valence': elem.valence_electrons
        }
    except Exception as e:
        raise ValueError(f"Invalid element symbol '{symbol}': {e}")

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string into a dictionary of element: fraction.
    
    Args:
        composition_str: String like "Zr50Cu40Al10" or "Zr50.0 Cu40.0 Al10.0"
        
    Returns:
        Dictionary mapping element symbols to their atomic fractions.
        
    Raises:
        ValueError: If parsing fails
    """
    import re
    
    # Handle different formats: Zr50Cu40Al10 or Zr50.0 Cu40.0 Al10.0
    # Split by element symbol (capital letter followed by optional lowercase)
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")
    
    composition = {}
    total = 0.0
    
    for symbol, fraction in matches:
        fraction = float(fraction)
        composition[symbol] = fraction
        total += fraction
    
    # Normalize to sum to 1.0 if not already
    if total > 0 and abs(total - 1.0) > 0.01:
        # Assume input is in atomic percent, normalize
        for symbol in composition:
            composition[symbol] /= total
            
    return composition

def calculate_weighted_mean_radius(composition: Dict[str, float]) -> float:
    """
    Calculate the weighted mean atomic radius (Angstrom).
    
    This is a diagnostic metric only and should NOT be used as a predictor.
    
    Args:
        composition: Dictionary of element: atomic_fraction
        
    Returns:
        Weighted mean radius in Angstrom
    """
    total_radius = 0.0
    total_fraction = 0.0
    
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        # Convert pm to Angstrom (1 Angstrom = 100 pm)
        radius_angstrom = props['radius'] / 100.0
        total_radius += radius_angstrom * fraction
        total_fraction += fraction
    
    if total_fraction == 0:
        raise ValueError("Total composition fraction is zero")
        
    return total_radius / total_fraction

def calculate_radius_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate atomic radius mismatch (delta).
    
    Formula: delta = sqrt(sum(c_i * (1 - r_i / r_avg)^2))
    
    Args:
        composition: Dictionary of element: atomic_fraction
        
    Returns:
        Radius mismatch value (dimensionless)
    """
    radii = []
    fractions = []
    
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        radii.append(props['radius'])
        fractions.append(fraction)
    
    radii = np.array(radii)
    fractions = np.array(fractions)
    
    r_avg = np.sum(fractions * radii)
    
    if r_avg == 0:
        return 0.0
    
    delta = np.sqrt(np.sum(fractions * ((1 - radii / r_avg) ** 2)))
    return delta

def calculate_electronegativity_difference(composition: Dict[str, float]) -> float:
    """
    Calculate electronegativity difference (delta_chi).
    
    Formula: delta_chi = sqrt(sum(c_i * (chi_i - chi_avg)^2))
    
    Args:
        composition: Dictionary of element: atomic_fraction
        
    Returns:
        Electronegativity difference (Pauling units)
    """
    electronegativities = []
    fractions = []
    
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        if props['electronegativity'] is None:
            # Fallback if electronegativity is not available
            electronegativities.append(0.0)
        else:
            electronegativities.append(props['electronegativity'])
        fractions.append(fraction)
    
    electronegativities = np.array(electronegativities)
    fractions = np.array(fractions)
    
    chi_avg = np.sum(fractions * electronegativities)
    
    delta_chi = np.sqrt(np.sum(fractions * ((electronegativities - chi_avg) ** 2)))
    return delta_chi

def calculate_vec(composition: Dict[str, float]) -> float:
    """
    Calculate Valence Electron Concentration (VEC).
    
    Formula: VEC = sum(c_i * VEC_i)
    
    Args:
        composition: Dictionary of element: atomic_fraction
        
    Returns:
        VEC value (electrons per atom)
    """
    vec_sum = 0.0
    
    for symbol, fraction in composition.items():
        props = get_element_properties(symbol)
        # Handle cases where valence electrons might be None
        valence = props['valence'] if props['valence'] is not None else 0.0
        vec_sum += fraction * valence
        
    return vec_sum

def compute_descriptors(composition_str: str) -> Dict[str, float]:
    """
    Compute all descriptors for a given composition.
    
    Args:
        composition_str: Composition string (e.g., "Zr50Cu40Al10")
        
    Returns:
        Dictionary of descriptor names to values
    """
    composition = parse_composition(composition_str)
    
    return {
        'radius_mismatch': calculate_radius_mismatch(composition),
        'electronegativity_diff': calculate_electronegativity_difference(composition),
        'VEC': calculate_vec(composition),
        'weighted_mean_radius': calculate_weighted_mean_radius(composition)  # Diagnostic only
    }

def process_dataframe(df: pd.DataFrame, composition_col: str = 'composition') -> pd.DataFrame:
    """
    Process a DataFrame to add descriptor columns.
    
    Args:
        df: Input DataFrame with composition column
        composition_col: Name of the composition column
        
    Returns:
        DataFrame with added descriptor columns
    """
    descriptors = []
    
    for idx, row in df.iterrows():
        try:
            desc = compute_descriptors(row[composition_col])
            descriptors.append(desc)
        except Exception as e:
            logging.warning(f"Failed to compute descriptors for row {idx}: {e}")
            # Append NaN for failed rows
            descriptors.append({
                'radius_mismatch': np.nan,
                'electronegativity_diff': np.nan,
                'VEC': np.nan,
                'weighted_mean_radius': np.nan
            })
    
    desc_df = pd.DataFrame(descriptors)
    result = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    
    return result

def save_diagnostic_log(weighted_mean_radius: float, output_path: Path) -> None:
    """
    Save the weighted mean radius to the diagnostic log.
    
    This function implements T021: Calculate 'weighted mean radius' for 
    diagnostic logging only (FR-002, exclude from model).
    
    Args:
        weighted_mean_radius: The calculated weighted mean radius in Angstrom
        output_path: Path to save the JSON file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    diagnostic_data = {
        "weighted_mean_radius": float(weighted_mean_radius)
    }
    
    with open(output_path, 'w') as f:
        json.dump(diagnostic_data, f, indent=2)
    
    logging.info(f"Saved diagnostic log to {output_path}")

def save_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save computed descriptors to CSV, excluding 'weighted_mean_radius'.
    
    Args:
        df: DataFrame with descriptor columns
        output_path: Path to save the CSV file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a copy to avoid modifying original
    df_to_save = df.copy()
    
    # Drop 'weighted_mean_radius' as it is diagnostic only and must not be used as predictor
    if 'weighted_mean_radius' in df_to_save.columns:
        df_to_save = df_to_save.drop(columns=['weighted_mean_radius'])
    
    df_to_save.to_csv(output_path, index=False)
    logging.info(f"Saved descriptors to {output_path}")

def main():
    """
    Main entry point for descriptor computation.
    
    This script:
    1. Loads cleaned data from data/processed/cleaned_mg.csv
    2. Computes descriptors
    3. Saves diagnostic log (weighted_mean_radius) to data/processed/diagnostic_log.json
    4. Saves descriptors (excluding weighted_mean_radius) to data/processed/descriptors.csv
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_project_root() / 'logs' / 'descriptors.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    project_root = get_project_root()
    cleaned_data_path = project_root / 'data' / 'processed' / 'cleaned_mg.csv'
    diagnostic_log_path = project_root / 'data' / 'processed' / 'diagnostic_log.json'
    descriptors_path = project_root / 'data' / 'processed' / 'descriptors.csv'
    
    # Verify input file exists
    if not cleaned_data_path.exists():
        logger.error(f"Cleaned data file not found: {cleaned_data_path}")
        sys.exit(1)
    
    # Load cleaned data
    logger.info(f"Loading cleaned data from {cleaned_data_path}")
    df = pd.read_csv(cleaned_data_path)
    logger.info(f"Loaded {len(df)} records")
    
    if df.empty:
        logger.error("Cleaned data is empty. Cannot compute descriptors.")
        sys.exit(1)
    
    # Check for composition column
    if 'composition' not in df.columns:
        logger.error("Composition column not found in cleaned data.")
        sys.exit(1)
    
    # Compute descriptors
    logger.info("Computing descriptors...")
    df_with_descriptors = process_dataframe(df, composition_col='composition')
    
    # Calculate weighted mean radius for the dataset (average of all samples)
    # This is for diagnostic logging only
    if 'weighted_mean_radius' in df_with_descriptors.columns:
        # Filter out NaN values
        valid_radii = df_with_descriptors['weighted_mean_radius'].dropna()
        if len(valid_radii) > 0:
            avg_weighted_mean_radius = valid_radii.mean()
            logger.info(f"Average weighted mean radius: {avg_weighted_mean_radius:.4f} Angstrom")
            
            # Save diagnostic log (T021)
            save_diagnostic_log(avg_weighted_mean_radius, diagnostic_log_path)
        else:
            logger.warning("No valid weighted_mean_radius values found. Skipping diagnostic log.")
    else:
        logger.warning("weighted_mean_radius column not found. Skipping diagnostic log.")
    
    # Save descriptors (excluding weighted_mean_radius) (T026)
    save_descriptors(df_with_descriptors, descriptors_path)
    
    logger.info("Descriptor computation completed successfully.")

if __name__ == '__main__':
    main()
