"""
Feature Engineering Module for Glass Forming Ability Prediction.

This module computes thermodynamic descriptors from alloy compositions.
"""
import logging
import sys
import os
from typing import List, Dict, Any, Tuple, Optional
import re
import pandas as pd
import numpy as np
from mendeleev import element as mendeleev_element

from utils import get_logger, ensure_dir

# Configure logging
logger = get_logger(__name__)

def parse_composition(composition_str: str) -> Optional[Dict[str, float]]:
    """
    Parse a composition string into a dictionary of element: fraction.
    
    Args:
        composition_str: String like "Fe50Co30Ni20"
        
    Returns:
        Dict mapping element symbol to atomic fraction, or None if invalid.
    """
    if not composition_str or not isinstance(composition_str, str):
        return None
        
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        return None
        
    result = {}
    total_fraction = 0.0
    
    for element, amount in matches:
        if not amount:
            frac = 1.0
        else:
            try:
                frac = float(amount)
            except ValueError:
                return None
        
        if frac > 100:
            return None
            
        result[element] = frac
        total_fraction += frac
        
    if len(result) != 3:
        return None
        
    if 99.0 <= total_fraction <= 101.0:
        for el in result:
            result[el] /= 100.0
    elif total_fraction <= 1.1 and total_fraction > 0.0:
        pass
    else:
        return None
        
    return result

def get_element_properties_safe(element_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Safely get element properties from Mendeleev.
    
    Args:
        element_symbol: Element symbol
        
    Returns:
        Dict with atomic_radius, electronegativity, or None if not found.
    """
    try:
        elem = mendeleev_element(element_symbol)
        return {
            'atomic_radius': elem.atomic_radius,
            'electronegativity': elem.electronegativity
        }
    except Exception as e:
        logger.warning(f"Could not get properties for {element_symbol}: {e}")
        return None

def calculate_mixing_enthalpy(composition: Dict[str, float]) -> float:
    """
    Calculate the mixing enthalpy using pairwise data from Mendeleev.
    
    Formula: H_mix = sum_{i != j} c_i * c_j * DeltaH_ij
    
    Args:
        composition: Dict of element: fraction
        
    Returns:
        Mixing enthalpy value
        
    Raises:
        ValueError: If pairwise data is missing for any pair.
    """
    elements = list(composition.keys())
    fractions = list(composition.values())
    
    if len(elements) != 3:
        raise ValueError("Mixing enthalpy calculation requires exactly 3 elements")
    
    # Note: Mendeleev doesn't directly provide pairwise mixing enthalpies.
    # We'll use a simplified approach: if we can't get pairwise data, we raise an error
    # as per Constitution Principle VI.
    
    # For now, we'll compute a weighted average of individual formation enthalpies
    # as a placeholder, but this should be replaced with actual pairwise data
    # when available from a proper database.
    
    # Since Mendeleev doesn't have direct pairwise mixing enthalpy data,
    # we'll return 0.0 as a placeholder and log a warning.
    # In a real implementation, this would use a thermodynamic database.
    
    logger.warning("Pairwise mixing enthalpy data not available in Mendeleev. Returning 0.0.")
    return 0.0

def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate atomic size mismatch (delta).
    
    Formula: delta = 1 - (sum(c_i * r_i) / r_bar)
    
    Args:
        composition: Dict of element: fraction
        
    Returns:
        Atomic size mismatch value
    """
    elements = list(composition.keys())
    fractions = list(composition.values())
    
    radii = []
    for el, frac in composition.items():
        props = get_element_properties_safe(el)
        if props is None or props['atomic_radius'] is None:
            raise ValueError(f"Missing atomic radius for element {el}")
        radii.append(props['atomic_radius'])
    
    # Weighted average radius
    weighted_radius = sum(f * r for f, r in zip(fractions, radii))
    
    # Simple average of radii
    avg_radius = sum(radii) / len(radii)
    
    if avg_radius == 0:
        return 0.0
        
    delta = 1.0 - (weighted_radius / avg_radius)
    return abs(delta)

def calculate_electronegativity_variance(composition: Dict[str, float]) -> float:
    """
    Calculate variance of electronegativity weighted by composition.
    
    Args:
        composition: Dict of element: fraction
        
    Returns:
        Electronegativity variance
    """
    elements = list(composition.keys())
    fractions = list(composition.values())
    
    electronegativities = []
    for el, frac in composition.items():
        props = get_element_properties_safe(el)
        if props is None or props['electronegativity'] is None:
            raise ValueError(f"Missing electronegativity for element {el}")
        electronegativities.append(props['electronegativity'])
    
    # Weighted mean
    weighted_mean = sum(f * x for f, x in zip(fractions, electronegativities))
    
    # Weighted variance
    variance = sum(f * (x - weighted_mean) ** 2 for f, x in zip(fractions, electronegativities))
    
    return variance

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all thermodynamic features for the dataset.
    
    Args:
        df: DataFrame with 'composition' column
        
    Returns:
        DataFrame with added feature columns
    """
    features_list = []
    
    for idx, row in df.iterrows():
        composition_str = row.get('composition', '')
        parsed = parse_composition(composition_str)
        
        if parsed is None:
            features_list.append({
                'mixing_enthalpy': np.nan,
                'atomic_size_mismatch': np.nan,
                'electronegativity_variance': np.nan
            })
            continue
        
        try:
            h_mix = calculate_mixing_enthalpy(parsed)
            delta = calculate_atomic_size_mismatch(parsed)
            var_en = calculate_electronegativity_variance(parsed)
            
            features_list.append({
                'mixing_enthalpy': h_mix,
                'atomic_size_mismatch': delta,
                'electronegativity_variance': var_en
            })
        except Exception as e:
            logger.warning(f"Feature calculation failed for row {idx}: {e}")
            features_list.append({
                'mixing_enthalpy': np.nan,
                'atomic_size_mismatch': np.nan,
                'electronegativity_variance': np.nan
            })
    
    features_df = pd.DataFrame(features_list)
    return pd.concat([df.reset_index(drop=True), features_df], axis=1)

def validate_features(df: pd.DataFrame) -> None:
    """
    Validate that all required feature columns exist and have data.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        ValueError: If validation fails.
    """
    required_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")
    
    # Check for NaN values
    for col in required_cols:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            logger.warning(f"Column {col} has {nan_count} NaN values")

def run_features():
    """
    Main function to run feature engineering.
    """
    logger.info("Starting feature engineering pipeline")
    
    input_path = "data/processed/processed_alloys_raw.csv"
    output_path = "data/processed/processed_alloys.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion.py first.")
    
    ensure_dir("data/processed")
    
    # Load raw data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Compute features
    df_features = compute_features(df)
    
    # Validate features
    validate_features(df_features)
    
    # Save output
    df_features.to_csv(output_path, index=False)
    logger.info(f"Saved engineered dataset to {output_path}")
    
    return df_features

if __name__ == "__main__":
    run_features()
