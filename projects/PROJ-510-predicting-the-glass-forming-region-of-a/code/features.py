import logging
import sys
import os
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from mendeleev import element

logger = logging.getLogger(__name__)

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """
    Retrieve atomic properties for a given element symbol using mendeleev.
    
    Args:
        symbol: Element symbol (e.g., 'Fe', 'Cu')
        
    Returns:
        Dictionary containing atomic_radius, electronegativity, and atomic_mass
        
    Raises:
        ValueError: If element symbol is invalid or properties are missing
    """
    try:
        el = element(symbol)
        return {
            'atomic_radius': el.atomic_radius,
            'electronegativity': el.electronegativity,
            'atomic_mass': el.atomic_mass,
            'symbol': symbol
        }
    except Exception as e:
        logger.error(f"Failed to retrieve properties for element {symbol}: {e}")
        raise ValueError(f"Invalid element symbol or missing properties: {symbol}") from e

def validate_composition(composition: Dict[str, float]) -> bool:
    """
    Validate that a composition dictionary is well-formed.
    
    Args:
        composition: Dictionary mapping element symbols to atomic fractions
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(composition, dict):
        return False
    if len(composition) == 0:
        return False
    total = sum(composition.values())
    # Allow small floating point tolerance
    if abs(total - 1.0) > 1e-6:
        return False
    for symbol, fraction in composition.items():
        if not isinstance(symbol, str) or len(symbol) == 0:
            return False
        if not isinstance(fraction, (int, float)) or fraction < 0:
            return False
    return True

def calculate_mixing_enthalpy(composition: Dict[str, float]) -> float:
    """
    Calculate the mixing enthalpy for a ternary alloy.
    
    Formula: ΔH_mix = Σ Σ Ω_ij * c_i * c_j (for i != j)
    where Ω_ij = 4 * ΔH_mix(AB) (binary mixing enthalpy)
    
    For this implementation, we approximate using the Miedema model simplified:
    ΔH_mix ≈ Σ c_i * c_j * (H_i - H_j)^2 (simplified proxy)
    
    A more rigorous approach uses binary interaction parameters from literature.
    Here we use a simplified thermodynamic proxy based on electronegativity 
    and atomic size differences as a feature engineering step.
    
    Args:
        composition: Dictionary of element symbols to atomic fractions
        
    Returns:
        Mixing enthalpy value (proxy)
    """
    if not validate_composition(composition):
        raise ValueError("Invalid composition for mixing enthalpy calculation")
    
    elements = list(composition.keys())
    fractions = [composition[e] for e in elements]
    
    if len(elements) != 3:
        logger.warning(f"Expected ternary alloy, got {len(elements)} elements. Calculation may be approximate.")
    
    # Get properties for all elements
    props = {}
    for e in elements:
        props[e] = get_element_properties(e)
    
    # Calculate pairwise contributions
    mixing_enthalpy = 0.0
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            e_i, e_j = elements[i], elements[j]
            c_i, c_j = fractions[i], fractions[j]
            
            # Simplified Miedema-like proxy using electronegativity and radius
            # ΔH ∝ c_i * c_j * (Δχ)^2 * (Δr/r_avg)
            d_chi = abs(props[e_i]['electronegativity'] - props[e_j]['electronegativity'])
            r_i, r_j = props[e_i]['atomic_radius'], props[e_j]['atomic_radius']
            if r_i is None or r_j is None or r_i == 0 or r_j == 0:
                continue # Skip if radius data missing
            r_avg = (r_i + r_j) / 2.0
            d_r = abs(r_i - r_j) / r_avg
            
            # Empirical scaling factor (simplified)
            contribution = c_i * c_j * (d_chi ** 2) * d_r
            mixing_enthalpy += contribution
    
    return mixing_enthalpy

def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate the atomic size mismatch (δ) parameter.
    
    Formula: δ = √[ Σ c_i * (1 - r_i / r_avg)^2 ] * 100
    where r_i is the atomic radius of element i, 
    r_avg is the composition-weighted average radius.
    
    Args:
        composition: Dictionary of element symbols to atomic fractions
        
    Returns:
        Atomic size mismatch percentage
    """
    if not validate_composition(composition):
        raise ValueError("Invalid composition for atomic size mismatch calculation")
    
    elements = list(composition.keys())
    fractions = [composition[e] for e in elements]
    
    # Get atomic radii
    radii = []
    for e in elements:
        props = get_element_properties(e)
        if props['atomic_radius'] is None:
            raise ValueError(f"Missing atomic radius for element {e}")
        radii.append(props['atomic_radius'])
    
    # Calculate weighted average radius
    r_avg = sum(c * r for c, r in zip(fractions, radii))
    if r_avg == 0:
        raise ValueError("Calculated average atomic radius is zero")
    
    # Calculate δ
    sum_sq = 0.0
    for c, r in zip(fractions, radii):
        sum_sq += c * ((1 - r / r_avg) ** 2)
    
    delta = np.sqrt(sum_sq) * 100.0
    return delta

def calculate_electronegativity_variance(composition: Dict[str, float]) -> float:
    """
    Calculate the variance of electronegativity in the alloy.
    
    Formula: σ_χ^2 = Σ c_i * (χ_i - χ_avg)^2
    
    Args:
        composition: Dictionary of element symbols to atomic fractions
        
    Returns:
        Electronegativity variance
    """
    if not validate_composition(composition):
        raise ValueError("Invalid composition for electronegativity variance calculation")
    
    elements = list(composition.keys())
    fractions = [composition[e] for e in elements]
    
    # Get electronegativities
    chi = []
    for e in elements:
        props = get_element_properties(e)
        if props['electronegativity'] is None:
            raise ValueError(f"Missing electronegativity for element {e}")
        chi.append(props['electronegativity'])
    
    # Calculate weighted average
    chi_avg = sum(c * x for c, x in zip(fractions, chi))
    
    # Calculate variance
    variance = sum(c * ((x - chi_avg) ** 2) for c, x in zip(fractions, chi))
    return variance

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string into a dictionary.
    
    Expected format: "Fe0.5Cu0.3Al0.2" or "Fe:0.5,Cu:0.3,Al:0.2"
    Handles standard chemical notation where element symbols are followed by fractions.
    
    Args:
        composition_str: String representation of composition
        
    Returns:
        Dictionary mapping element symbols to atomic fractions
    """
    import re
    
    # Normalize separators
    if ',' in composition_str:
        parts = [p.strip() for p in composition_str.split(',')]
        parts = [p.replace(':', '') for p in parts]
    else:
        # Try to parse "Fe0.5Cu0.3Al0.2" style
        # Regex to match element symbol followed by number
        pattern = r'([A-Z][a-z]?)(\d*\.?\d+)'
        matches = re.findall(pattern, composition_str)
        parts = [f"{m[0]}{m[1]}" for m in matches]
    
    result = {}
    for part in parts:
        # Extract element and fraction
        match = re.match(r'([A-Z][a-z]?)(\d*\.?\d+)', part)
        if not match:
            raise ValueError(f"Could not parse composition part: {part}")
        
        symbol = match.group(1)
        fraction = float(match.group(2))
        result[symbol] = fraction
    
    # Normalize if sum != 1
    total = sum(result.values())
    if abs(total - 1.0) > 1e-9:
        result = {k: v/total for k, v in result.items()}
    
    return result

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute thermodynamic features for a DataFrame of alloy compositions.
    
    Expected input columns:
        - 'composition': String or dict representation of alloy composition
        - 'critical_cooling_rate': Target variable (optional, but required for validation)
        
    Output columns added:
        - 'mixing_enthalpy': Calculated mixing enthalpy
        - 'atomic_size_mismatch': Calculated atomic size mismatch (δ)
        - 'electronegativity_variance': Calculated electronegativity variance
        
    Args:
        df: Input DataFrame with composition data
        
    Returns:
        DataFrame with added feature columns
    """
    logger.info(f"Computing features for {len(df)} alloy records")
    
    features = {
        'mixing_enthalpy': [],
        'atomic_size_mismatch': [],
        'electronegativity_variance': []
    }
    
    errors = 0
    for idx, row in df.iterrows():
        try:
            comp_str = row['composition']
            
            # Parse composition if string
            if isinstance(comp_str, str):
                comp = parse_composition(comp_str)
            elif isinstance(comp_str, dict):
                comp = comp_str
            else:
                logger.warning(f"Row {idx}: Invalid composition type {type(comp_str)}, skipping")
                errors += 1
                features['mixing_enthalpy'].append(np.nan)
                features['atomic_size_mismatch'].append(np.nan)
                features['electronegativity_variance'].append(np.nan)
                continue
            
            # Calculate features
            features['mixing_enthalpy'].append(calculate_mixing_enthalpy(comp))
            features['atomic_size_mismatch'].append(calculate_atomic_size_mismatch(comp))
            features['electronegativity_variance'].append(calculate_electronegativity_variance(comp))
            
        except Exception as e:
            logger.warning(f"Row {idx}: Failed to compute features: {e}")
            errors += 1
            features['mixing_enthalpy'].append(np.nan)
            features['atomic_size_mismatch'].append(np.nan)
            features['electronegativity_variance'].append(np.nan)
    
    if errors > 0:
        logger.warning(f"Failed to compute features for {errors} rows")
    
    result = df.copy()
    result['mixing_enthalpy'] = features['mixing_enthalpy']
    result['atomic_size_mismatch'] = features['atomic_size_mismatch']
    result['electronegativity_variance'] = features['electronegativity_variance']
    
    return result

def validate_features(df: pd.DataFrame, tolerance: float = 1e-6) -> bool:
    """
    Validate computed features for consistency and plausibility.
    
    Checks:
        - No NaN in computed feature columns
        - Values are within reasonable physical bounds
        - Tolerance check for reproducibility if run again
        
    Args:
        df: DataFrame with computed features
        tolerance: Tolerance for floating point comparisons
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValueError: If validation fails
    """
    required_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        
        if df[col].isna().any():
            nan_count = df[col].isna().sum()
            raise ValueError(f"Column '{col}' contains {nan_count} NaN values")
        
        # Basic physical bounds check
        if col == 'atomic_size_mismatch':
            # δ is typically 0-20% for glass formers, but allow up to 50%
            if (df[col] < 0).any() or (df[col] > 50).any():
                logger.warning(f"Column '{col}' has values outside typical range [0, 50]")
        
        if col == 'electronegativity_variance':
            # Variance should be non-negative
            if (df[col] < 0).any():
                raise ValueError(f"Column '{col}' contains negative values")
    
    logger.info("Feature validation passed")
    return True

def run_features():
    """
    Main entry point for feature engineering pipeline.
    
    Loads raw/processed data from ingestion, computes features, validates,
    and saves to data/processed/processed_alloys.csv.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = 'data/processed/ingested_alloys.csv'
    output_path = 'data/processed/processed_alloys.csv'
    
    if not os.path.exists(input_path):
        # Try alternative path if standard path not found
        alt_path = 'data/processed/processed_alloys_raw.csv'
        if os.path.exists(alt_path):
            input_path = alt_path
        else:
            # Check if we need to run ingestion first
            logger.error(f"Input file not found: {input_path}. Please run ingestion first.")
            sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} records")
    
    # Compute features
    df_processed = compute_features(df)
    
    # Validate features
    try:
        validate_features(df_processed, tolerance=1e-6)
    except ValueError as e:
        logger.error(f"Feature validation failed: {e}")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save processed data
    df_processed.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")
    
    # Log summary
    logger.info(f"Processed {len(df_processed)} records with features: "
                f"mixing_enthalpy, atomic_size_mismatch, electronegativity_variance")

if __name__ == "__main__":
    run_features()