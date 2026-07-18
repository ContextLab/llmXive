import os
import sys
import math
import json
import logging
from pathlib import Path
import pandas as pd

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def get_data_path():
    config = get_config()
    return Path(config.get("data_dir", "data"))

def convert_k_to_half_life(k: float) -> float:
    """
    Convert rate constant (k) to half-life (t1/2).
    t1/2 = ln(2) / k
    """
    if k <= 0:
        raise ValueError("Rate constant k must be positive")
    return math.log(2) / k

def normalize_arrhenius(k: float, Ea: float, T: float, T_ref: float = 298.15) -> float:
    """
    Normalize rate constant using Arrhenius equation.
    Note: This is skipped in the current implementation as Ea is unavailable.
    """
    R = 8.314  # Gas constant in J/(mol*K)
    # k_ref = k * exp(Ea/R * (1/T - 1/T_ref))
    # Since Ea is unavailable, this function is not used
    raise NotImplementedError("Arrhenius normalization requires activation energy (Ea), which is unavailable.")

def check_data_coverage(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check the coverage of pH and Temperature columns in the dataset.
    """
    coverage = {
        'has_ph': 'ph' in df.columns,
        'has_temp': 'temp' in df.columns,
        'ph_missing_count': df['ph'].isna().sum() if 'ph' in df.columns else 0,
        'temp_missing_count': df['temp'].isna().sum() if 'temp' in df.columns else 0
    }
    return coverage

def standardize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize the dataset by converting rate constants to half-lives
    and filtering for standard conditions (25°C, pH 7.4).
    """
    # Convert rate constant to half-life if 'k' column exists
    if 'k' in df.columns:
        df['half_life'] = df['k'].apply(convert_k_to_half_life)
    elif 'half_life' not in df.columns:
        logger.warning("Neither 'k' nor 'half_life' column found. Cannot standardize.")
        return df

    # Check for covariates
    coverage = check_data_coverage(df)
    if coverage['has_ph'] or coverage['has_temp']:
        logger.info("Covariates (pH/Temp) found in dataset. Will attempt inclusion in analysis.")
    else:
        logger.warning("No covariates (pH/Temp) found. Skipping covariate inclusion.")

    # Filter for standard conditions (25°C = 298.15K, pH 7.4)
    # Assuming 'temp' is in Celsius and 'ph' is in pH units
    standard_mask = (df['temp'] == 25) & (df['ph'] == 7.4)
    standard_subset = df[standard_mask].copy()
    
    # Log the size of the standard subset
    logger.info(f"Standard subset size: {len(standard_subset)} out of {len(df)}")
    
    return standard_subset

def main():
    config = get_config()
    logger.info("Starting standardization")
    
    # Load data
    input_path = get_data_path() / "processed" / "merged_drugs.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    df = pd.read_csv(input_path)
    
    # Standardize
    standard_df = standardize_dataset(df)
    
    # Save standard subset
    output_path = get_data_path() / "processed" / "standard_subset.csv"
    standard_df.to_csv(output_path, index=False)
    logger.info(f"Saved standard subset to {output_path}")

if __name__ == "__main__":
    main()
