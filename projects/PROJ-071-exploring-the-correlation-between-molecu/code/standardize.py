import os
import sys
import math
import json
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime

from config import get_config
from logging_config import get_logger, log_pipeline_failure

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

def check_data_coverage(df: pd.DataFrame) -> dict:
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
    # Handle potential missing columns gracefully
    if 'temp' in df.columns and 'ph' in df.columns:
        standard_mask = (df['temp'] == 25) & (df['ph'] == 7.4)
        standard_subset = df[standard_mask].copy()
    else:
        # If columns missing, cannot filter by standard conditions.
        # Return the whole dataset but log warning.
        logger.warning("Missing 'temp' or 'ph' columns. Cannot filter for standard conditions.")
        standard_subset = df.copy()
    
    # Log the size of the standard subset
    logger.info(f"Standard subset size: {len(standard_subset)} out of {len(df)}")
    
    return standard_subset

def main():
    config = get_config()
    logger.info("Starting standardization")
    
    # Check Gate Status first
    gate_status_path = get_data_path() / "gate_status.json"
    if gate_status_path.exists():
        with open(gate_status_path, 'r') as f:
            gate_data = json.load(f)
            if gate_data.get("status") == "FAIL":
                logger.warning("Data Availability Gate failed. Skipping standardization.")
                log_pipeline_failure("standardize", "Skipped: Data Insufficient")
                return
    else:
        logger.warning("gate_status.json not found. Proceeding with caution.")

    # Load data
    input_path = get_data_path() / "processed" / "merged_drugs.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        log_pipeline_failure("standardize", f"Input file not found: {input_path}")
        return
    
    df = pd.read_csv(input_path)
    
    # Standardize
    standard_df = standardize_dataset(df)
    
    # Save standard subset
    output_path = get_data_path() / "processed" / "standard_subset.csv"
    standard_df.to_csv(output_path, index=False)
    logger.info(f"Saved standard subset to {output_path}")

    # T021b: Data Characteristics Table
    excluded_count = len(df) - len(standard_df)
    characteristics = {
        "total_records": len(df),
        "standard_records": len(standard_df),
        "excluded_records": excluded_count,
        "exclusion_reason": "Non-standard conditions (Temp != 25C or pH != 7.4)"
    }
    characteristics_path = get_data_path() / "processed" / "data_characteristics.csv"
    pd.DataFrame([characteristics]).to_csv(characteristics_path, index=False)
    logger.info(f"Saved data characteristics to {characteristics_path}")

    # T021c: Audit Trail Merge
    # Add a flag to the original df to indicate inclusion
    df['included_in_standard'] = df.index.isin(standard_df.index)
    full_processed_path = get_data_path() / "processed" / "full_processed_state.csv"
    df.to_csv(full_processed_path, index=False)
    logger.info(f"Saved full processed state to {full_processed_path}")

    # T022a: Sensitivity Analysis / Arrhenius Exclusion Log
    log_path = get_data_path() / "processed" / "analysis_log.txt"
    with open(log_path, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] Arrhenius normalization EXCLUDED: Activation Energy (Ea) data unavailable per plan.md.\n")
    logger.info(f"Appended Arrhenius exclusion log to {log_path}")

if __name__ == "__main__":
    main()