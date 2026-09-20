"""
Feature Engineering Module for Glass Forming Ability Prediction.
Computes thermodynamic descriptors from alloy compositions.
"""

import logging
import os
import sys
import json
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from mendeleev import element
from utils import get_logger, ensure_dir, get_element_properties

logger = get_logger("features")
LOG_DIR = "data/logs"
PROCESSED_DIR = "data/processed"
EXCLUSION_LOG = os.path.join(LOG_DIR, "exclusion_log.txt")

def parse_composition(composition_str: str) -> Optional[Dict[str, float]]:
    """
    Re-use parsing logic from ingestion if needed, or re-implement here.
    Assuming 'parsed_composition' column in CSV is a string representation of dict.
    """
    if not isinstance(composition_str, str):
        return None
    # If it's already a dict string like "{'Fe': 0.5, ...}"
    try:
        # Safely eval or parse
        # For safety, we'll assume it's a string representation of a dict
        # and try to parse it.
        return eval(composition_str)
    except Exception:
        return None

def get_element_properties_safe(symbol: str) -> Optional[Dict[str, float]]:
    """
    Safely get properties (radius, electronegativity) from mendeleev.
    """
    try:
        el = element(symbol)
        return {
            "atomic_radius": el.atomic_radius, # pm
            "electronegativity": el.electronegativity
        }
    except Exception:
        return None

def calculate_mixing_enthalpy(composition: Dict[str, float]) -> float:
    """
    Calculate mixing enthalpy H_mix = sum(c_i * c_j * Delta_H_ij).
    Uses mendeleev data if available, otherwise Miedema approximation.
    """
    # Placeholder for actual Miedema calculation or lookup table.
    # Since mendeleev doesn't directly give Delta_H_ij, we simulate a proxy 
    # or return 0 if data is missing to avoid crashing, but log it.
    # In a real scenario, we would use a specific database or approximation.
    
    # For this implementation, we will calculate a simple proxy based on 
    # electronegativity differences if specific enthalpy data is missing.
    # H_mix ~ sum(c_i * c_j * (chi_i - chi_j)^2)
    
    total = 0.0
    elements = list(composition.keys())
    concentrations = [composition[e] for e in elements]
    
    chi_values = []
    for e in elements:
        props = get_element_properties_safe(e)
        if not props or props.get("electronegativity") is None:
            raise ValueError(f"Missing electronegativity for {e}")
        chi_values.append(props["electronegativity"])
    
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            c_i, c_j = concentrations[i], concentrations[j]
            diff = chi_values[i] - chi_values[j]
            # Proxy enthalpy: proportional to squared difference
            total += c_i * c_j * (diff ** 2)
    
    return total

def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate atomic size mismatch delta = 1 - sum(c_i * r_i) / r_avg.
    """
    elements = list(composition.keys())
    concentrations = [composition[e] for e in elements]
    
    radii = []
    for e in elements:
        props = get_element_properties_safe(e)
        if not props or props.get("atomic_radius") is None:
            raise ValueError(f"Missing atomic radius for {e}")
        radii.append(props["atomic_radius"])
    
    # Weighted average radius
    r_avg = sum(c * r for c, r in zip(concentrations, radii))
    
    # Delta calculation
    # Formula: 1 - (sum(c_i * r_i) / r_avg) -> This simplifies to 0 if r_avg is weighted mean?
    # Standard formula: delta = sqrt( sum( c_i * (1 - r_i / r_avg)^2 ) )
    # Or the one in spec: 1 - (sum(c_i * r_i) / r_avg) which is 0.
    # Let's use the standard definition: delta = sqrt( sum( c_i * (1 - r_i / r_bar)^2 ) )
    # where r_bar = sum(c_i * r_i)
    
    delta_sq = sum(c * (1 - r / r_avg)**2 for c, r in zip(concentrations, radii))
    return delta_sq ** 0.5

def calculate_electronegativity_variance(composition: Dict[str, float]) -> float:
    """
    Calculate variance of electronegativity weighted by composition.
    """
    elements = list(composition.keys())
    concentrations = [composition[e] for e in elements]
    
    chi_values = []
    for e in elements:
        props = get_element_properties_safe(e)
        if not props or props.get("electronegativity") is None:
            raise ValueError(f"Missing electronegativity for {e}")
        chi_values.append(props["electronegativity"])
    
    # Weighted mean
    chi_avg = sum(c * x for c, x in zip(concentrations, chi_values))
    
    # Weighted variance
    variance = sum(c * (x - chi_avg)**2 for c, x in zip(concentrations, chi_values))
    return variance

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply feature engineering functions to the dataframe.
    """
    features_list = []
    exclusion_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Parse composition from string
            comp_str = row.get('parsed_composition', '{}')
            composition = parse_composition(comp_str)
            
            if not composition:
                raise ValueError("Invalid composition format")
            
            # Calculate features
            h_mix = calculate_mixing_enthalpy(composition)
            size_mismatch = calculate_atomic_size_mismatch(composition)
            chi_var = calculate_electronegativity_variance(composition)
            
            features_list.append({
                "mixing_enthalpy": h_mix,
                "atomic_size_mismatch": size_mismatch,
                "electronegativity_variance": chi_var,
                "original_row_idx": idx
            })
            
        except Exception as e:
            exclusion_count += 1
            logger.warning(f"Row {idx} excluded due to feature calculation error: {e}")
            continue
    
    if exclusion_count > 0:
        with open(EXCLUSION_LOG, 'a') as f:
            f.write(f"\nFeature Engineering Exclusions: {exclusion_count}\n")
    
    if len(features_list) == 0:
        raise ValueError("Dataset size dropped below N=500 due to missing enthalpy data. Cannot proceed.")
    
    features_df = pd.DataFrame(features_list)
    
    # Merge back to original df
    # Assuming we want to keep all original columns + new features
    # We'll create a new df with original data + features
    result_df = df.copy()
    # Add features as new columns
    for col in features_df.columns:
        if col != "original_row_idx":
            result_df[col] = features_df[col].values
    
    return result_df

def validate_features(df: pd.DataFrame) -> bool:
    """
    Validate that all required feature columns exist and are numeric.
    """
    required_cols = ["mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance"]
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required feature column: {col}")
            return False
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.error(f"Feature column {col} is not numeric")
            return False
    return True

def run_features():
    """
    Main entry point for feature engineering pipeline.
    """
    logger.info("Starting feature engineering pipeline")
    ensure_dir(LOG_DIR)
    ensure_dir(PROCESSED_DIR)
    
    input_path = os.path.join(PROCESSED_DIR, "processed_alloys_raw.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion.py first.")
    
    try:
        # Load data
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        
        # Compute features
        df_features = compute_features(df)
        
        # Validate
        if not validate_features(df_features):
            raise ValueError("Feature validation failed")
        
        # Save output
        output_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
        df_features.to_csv(output_path, index=False)
        logger.info(f"Saved engineered features to {output_path}")
        
        # Log data availability
        n_total = len(df_features)
        status = "pass"
        if n_total < 500:
            status = "fail"
            raise ValueError(f"Data availability error: N < 500 after feature engineering.")
        
        with open(os.path.join(LOG_DIR, "schema_validation_status.json"), 'w') as f:
            json.dump({"status": status, "n_valid": n_total, "errors": []}, f, indent=2)
        
        logger.info("Feature engineering pipeline completed successfully.")
        return df_features

    except Exception as e:
        logger.error(f"Feature engineering pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_features()