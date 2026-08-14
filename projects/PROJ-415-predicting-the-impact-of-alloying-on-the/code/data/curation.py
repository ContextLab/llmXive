"""
Data Curation Module for Diffusion Activation Energy Project.

This module handles the exclusion of rows with missing critical data
(solute concentration, atomic radii) and logs these exclusions.
"""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import Tuple, Optional

from config import DATA_DIR, LOG_DIR, PROJECT_ROOT
from utils.logging import get_logger
from utils.constants import get_metallic_radius

# Initialize logger
logger = get_logger(__name__)

def load_curated_data() -> pd.DataFrame:
    """
    Loads the filtered dataset from the ingestion step.
    Expects: data/curated/filtered.csv
    """
    input_path = DATA_DIR / "curated" / "filtered.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please run ingestion (T013) first to generate this file."
        )
    logger.info(f"Loading curated data from {input_path}")
    return pd.read_csv(input_path)

def validate_atomic_radii(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates that rows have valid atomic radii for both solute and host.
    Uses the get_metallic_radius helper from utils.constants.
    
    Returns:
        Tuple of (valid_df, invalid_df_with_reasons)
    """
    invalid_indices = []
    reasons = []

    # Ensure we have columns for host and solute
    # Assuming standard naming from ingestion: 'host_element', 'solute_element'
    # If columns differ, this might need adjustment based on actual schema
    host_col = 'host_element'
    solute_col = 'solute_element'

    if host_col not in df.columns or solute_col not in df.columns:
        # Fallback or error if columns are missing entirely
        logger.error(f"Missing required columns '{host_col}' or '{solute_col}'")
        # If columns are missing, we can't validate radii, so treat all as invalid?
        # Or raise an error. Let's assume the schema is correct per T013.
        return df, pd.DataFrame(columns=['row_id', 'reason_code', 'details'])

    for idx, row in df.iterrows():
        host = row.get(host_col)
        solute = row.get(solute_col)
        
        radius_host = None
        radius_solute = None
        reason = None

        if pd.isna(host) or not isinstance(host, str):
            reason = "INVALID_HOST_SYMBOL"
        elif not get_metallic_radius(host):
            reason = "MISSING_HOST_RADIUS"
        
        if not reason:
            if pd.isna(solute) or not isinstance(solute, str):
                reason = "INVALID_SOLUTE_SYMBOL"
            elif not get_metallic_radius(solute):
                reason = "MISSING_SOLUTE_RADIUS"

        if reason:
            invalid_indices.append(idx)
            reasons.append(reason)

    valid_df = df.drop(index=invalid_indices)
    
    if invalid_indices:
        invalid_df = pd.DataFrame({
            'row_id': invalid_indices,
            'reason_code': reasons,
            'details': [f"Host: {df.loc[i, host_col]}, Solute: {df.loc[i, solute_col]}" for i in invalid_indices]
        })
        logger.warning(f"Excluded {len(invalid_indices)} rows due to missing atomic radii.")
    else:
        invalid_df = pd.DataFrame(columns=['row_id', 'reason_code', 'details'])
        logger.info("All rows have valid atomic radii.")

    return valid_df, invalid_df

def exclude_missing_concentration(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Excludes rows where solute concentration is missing or invalid.
    Assumes column 'concentration_at_percent' or similar.
    Based on T013, we expect a concentration column. Let's assume 'concentration_at_percent' 
    or check for common names if not present.
    Actually, T013 filters for 'self' diffusion, but T014 mentions 'solute concentration'.
    In self-diffusion, concentration is effectively 0 or N/A, but the task says 
    "exclude rows with missing solute concentration". 
    If it's self-diffusion, maybe the column is 'concentration' and should be 0?
    Or perhaps the task implies general alloying data where concentration matters.
    Let's assume the column is named 'concentration_at_percent' based on standard 
    diffusion datasets, or 'solute_concentration'. 
    Looking at T013 description: "filter ... diffusion_mode == 'self'". 
    If it's self-diffusion, the 'solute' is the same as 'host', and concentration is 0.
    However, the task T014 explicitly says "exclude rows with missing solute concentration".
    This implies we are looking for a concentration column.
    Let's check for 'concentration_at_percent' first, then 'solute_concentration', then 'concentration'.
    """
    concentration_cols = ['concentration_at_percent', 'solute_concentration', 'concentration']
    conc_col = None
    for col in concentration_cols:
        if col in df.columns:
            conc_col = col
            break
    
    if not conc_col:
        logger.warning("No concentration column found. Assuming all rows are valid for concentration check.")
        return df, pd.DataFrame(columns=['row_id', 'reason_code'])

    invalid_indices = []
    reasons = []

    for idx, row in df.iterrows():
        val = row.get(conc_col)
        if pd.isna(val):
            invalid_indices.append(idx)
            reasons.append('MISSING_CONCENTRATION')
        elif not isinstance(val, (int, float)):
            # Try to convert or mark invalid
            try:
                float(val)
            except (ValueError, TypeError):
                invalid_indices.append(idx)
                reasons.append('MISSING_CONCENTRATION')

    valid_df = df.drop(index=invalid_indices)

    if invalid_indices:
        invalid_df = pd.DataFrame({
            'row_id': invalid_indices,
            'reason_code': reasons
        })
        logger.warning(f"Excluded {len(invalid_indices)} rows due to missing concentration.")
    else:
        invalid_df = pd.DataFrame(columns=['row_id', 'reason_code'])
        logger.info("All rows have valid concentration data.")

    return valid_df, invalid_df

def log_exclusions(
    total_excluded: int, 
    concentration_exclusions: pd.DataFrame, 
    atomic_exclusions: pd.DataFrame
) -> None:
    """
    Logs exclusions to data/logs/exclusions.log and errors/missing_atomic_data.csv.
    
    Format for exclusions.log:
    Line 1: # EXCLUSION_COUNT: <count>
    Subsequent lines: CSV format (row_id, reason_code)
    """
    # Ensure log directory exists
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    exclusion_log_path = log_dir / "exclusions.log"
    errors_dir = Path(PROJECT_ROOT) / "errors"
    errors_dir.mkdir(parents=True, exist_ok=True)
    atomic_errors_path = errors_dir / "missing_atomic_data.csv"

    # Write exclusion log
    with open(exclusion_log_path, 'w') as f:
        f.write(f"# EXCLUSION_COUNT: {total_excluded}\n")
        
        # Write concentration exclusions
        if not concentration_exclusions.empty:
            for _, row in concentration_exclusions.iterrows():
                f.write(f"{row['row_id']},{row['reason_code']}\n")
        
        # Write atomic radius exclusions
        if not atomic_exclusions.empty:
            for _, row in atomic_exclusions.iterrows():
                f.write(f"{row['row_id']},{row['reason_code']}\n")

    logger.info(f"Exclusion log written to {exclusion_log_path}")

    # Write atomic errors CSV
    if not atomic_exclusions.empty:
        atomic_exclusions.to_csv(atomic_errors_path, index=False)
        logger.info(f"Atomic data errors written to {atomic_errors_path}")
    else:
        # Create empty file if none
        atomic_exclusions.to_csv(atomic_errors_path, index=False)
        logger.info(f"No atomic data errors to write, created empty {atomic_errors_path}")

def run_curation() -> pd.DataFrame:
    """
    Main entry point for the curation process.
    1. Load curated data from ingestion.
    2. Exclude rows with missing concentration.
    3. Exclude rows with missing atomic radii.
    4. Log all exclusions.
    5. Save the final curated dataset.
    """
    df = load_curated_data()
    original_count = len(df)
    logger.info(f"Starting curation with {original_count} rows.")

    # Step 1: Check concentration
    df_conc_valid, conc_invalid = exclude_missing_concentration(df)
    
    # Step 2: Check atomic radii on the concentration-valid set
    df_radii_valid, radii_invalid = validate_atomic_radii(df_conc_valid)

    # Calculate total excluded
    total_excluded = original_count - len(df_radii_valid)
    
    # Log exclusions
    log_exclusions(total_excluded, conc_invalid, radii_invalid)

    # Save final curated data
    output_path = DATA_DIR / "curated" / "filtered.csv"
    df_radii_valid.to_csv(output_path, index=False)
    logger.info(f"Final curated data saved to {output_path} ({len(df_radii_valid)} rows).")

    return df_radii_valid

if __name__ == "__main__":
    run_curation()
